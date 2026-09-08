"""
E2PaymentsProvider — Cliente HTTP para a API do E2Payments (Explicador Inc.).

Implementa IPaymentGateway usando httpx.AsyncClient.

Referência: https://e2payments.explicador.co.mz/docs/api
"""
import logging
import time
from typing import Optional

import httpx

from app.modules.payments.domain.repositories.payment_gateway import (
    IPaymentGateway,
    PaymentGatewayResult,
    PaymentStatusResult,
)

logger = logging.getLogger(__name__)

# Cache de token em memória (renovado a cada 24h para segurança,
# mesmo que o token do E2Payments dure 1 ano)
_TOKEN_CACHE: dict = {
    "value": None,
    "expires_at": 0.0,
}
_TOKEN_TTL_SECONDS = 24 * 60 * 60  # 24 horas


class E2PaymentsProvider(IPaymentGateway):
    """
    Provider E2Payments que implementa IPaymentGateway.

    Todas as chamadas são HTTP POST (mesmo as de consulta — padrão E2Payments).
    Autenticação via OAuth2 client_credentials (token cacheado 24h).
    """

    def __init__(
        self,
        base_url: str,
        client_id: str,
        client_secret: str,
        wallet_id: str,
    ):
        self.base_url = base_url.rstrip("/")
        self.client_id = client_id
        self.client_secret = client_secret
        self.wallet_id = wallet_id

    # ─── Token Management ────────────────────────────────────────────────────

    async def _get_token(self) -> str:
        """Obtém o access token cacheado. Renova se expirado."""
        global _TOKEN_CACHE

        now = time.time()
        if _TOKEN_CACHE["value"] and now < _TOKEN_CACHE["expires_at"]:
            return _TOKEN_CACHE["value"]

        logger.info("E2Payments: A renovar access token...")

        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(
                f"{self.base_url}/oauth/token",
                json={
                    "grant_type": "client_credentials",
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                },
                headers={"Accept": "application/json", "Content-Type": "application/json"},
            )

        response.raise_for_status()
        data = response.json()

        token_value = f"{data['token_type']} {data['access_token']}"
        _TOKEN_CACHE = {
            "value": token_value,
            "expires_at": now + _TOKEN_TTL_SECONDS,
        }

        logger.info("E2Payments: Token renovado com sucesso (válido 24h)")
        return token_value

    async def _auth_headers(self) -> dict:
        """Retorna os headers de autenticação para todas as chamadas autenticadas."""
        token = await self._get_token()
        return {
            "Authorization": token,
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

    # ─── C2B — STK Push ──────────────────────────────────────────────────────

    async def initiate_c2b(
        self,
        amount: float,
        phone: str,
        reference: str,
    ) -> PaymentGatewayResult:
        """
        Inicia uma transacção C2B Mpesa (STK Push).

        O telemóvel do cliente recebe um pop-up pedindo confirmação do PIN.
        A transacção só é confirmada quando o cliente insere o PIN.

        Args:
            amount:    Montante em MZN.
            phone:     9 dígitos sem código de país (ex: 848512345).
            reference: String sem espaços, aparece no SMS de confirmação.
        """
        endpoint = f"{self.base_url}/v1/c2b/mpesa-payment/{self.wallet_id}"
        payload = {
            "client_id": self.client_id,
            "amount": str(int(amount)),  # E2Payments aceita string ou int
            "phone": phone,
            "reference": reference,
        }

        logger.info(
            f"E2Payments C2B: Iniciando pagamento | amount={amount} phone={phone} ref={reference}"
        )

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                headers = await self._auth_headers()
                response = await client.post(endpoint, json=payload, headers=headers)

            logger.info(
                f"E2Payments C2B: HTTP {response.status_code} | ref={reference} | body={response.text[:200]}"
            )

            # E2Payments retorna 200 ou 201 em caso de sucesso
            if response.status_code in (200, 201):
                return PaymentGatewayResult(
                    success=True,
                    gateway_reference=reference,
                    raw_response=response.json() if response.text else {},
                )

            # Erro do gateway (400/401/403/500)
            error_body = response.text[:500]
            logger.error(
                f"E2Payments C2B: Erro {response.status_code} | ref={reference} | body={error_body}"
            )
            return PaymentGatewayResult(
                success=False,
                gateway_reference=reference,
                raw_response={"status_code": response.status_code, "body": error_body},
                error_message=f"Gateway retornou HTTP {response.status_code}: {error_body}",
            )

        except httpx.TimeoutException:
            logger.error(f"E2Payments C2B: Timeout na chamada | ref={reference}")
            return PaymentGatewayResult(
                success=False,
                gateway_reference=reference,
                error_message="Timeout ao comunicar com o gateway E2Payments",
            )
        except httpx.RequestError as exc:
            logger.error(f"E2Payments C2B: Erro de rede | ref={reference} | {exc}")
            return PaymentGatewayResult(
                success=False,
                gateway_reference=reference,
                error_message=f"Erro de rede: {exc}",
            )

    # ─── Consulta de Pagamentos (para reconciliação) ──────────────────────────

    async def get_recent_confirmed_payments(
        self, limit: int = 20
    ) -> list[PaymentStatusResult]:
        """
        Obtém os pagamentos Mpesa mais recentes do E2Payments para reconciliação.

        O E2Payments não tem webhooks — este método é chamado periodicamente
        para detectar pagamentos confirmados e ligar ao pipeline interno.
        """
        endpoint = f"{self.base_url}/v1/payments/mpesa/get/all/paginate/{limit}"

        logger.debug(f"E2Payments Polling: Consultando {limit} pagamentos recentes...")

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                headers = await self._auth_headers()
                response = await client.post(
                    endpoint,
                    json={"client_id": self.client_id},
                    headers=headers,
                )

            if response.status_code != 200:
                logger.warning(
                    f"E2Payments Polling: HTTP {response.status_code} ao consultar pagamentos"
                )
                return []

            data = response.json()
            # A resposta é paginada — os pagamentos estão em data["data"] ou na raiz
            raw_payments = data.get("data", data) if isinstance(data, dict) else data
            if not isinstance(raw_payments, list):
                raw_payments = []

            results = []
            for payment in raw_payments:
                # Campo "reference" identifica o pagamento no nosso sistema
                ref = payment.get("reference") or payment.get("referencia") or ""
                if not ref:
                    continue

                # Filtra apenas pagamentos confirmados/sucesso
                status_field = (
                    payment.get("status")
                    or payment.get("estado")
                    or payment.get("transaction_status")
                    or ""
                ).upper()

                confirmed = status_field in ("SUCCESS", "COMPLETED", "CONFIRMED", "PROCESSED")
                if not confirmed:
                    continue

                results.append(
                    PaymentStatusResult(
                        reference=ref,
                        confirmed=True,
                        amount=float(payment.get("amount") or payment.get("montante") or 0),
                        phone=str(payment.get("phone") or payment.get("msisdn") or ""),
                        gateway_data=payment,
                    )
                )

            logger.debug(
                f"E2Payments Polling: {len(results)} pagamentos confirmados de {len(raw_payments)} consultados"
            )
            return results

        except httpx.TimeoutException:
            logger.warning("E2Payments Polling: Timeout ao consultar pagamentos")
            return []
        except Exception as exc:
            logger.error(f"E2Payments Polling: Erro inesperado: {exc}")
            return []

    # ─── Utilitários ─────────────────────────────────────────────────────────

    async def list_wallets(self) -> Optional[dict]:
        """Lista as carteiras Mpesa associadas à conta. Útil para diagnóstico."""
        endpoint = f"{self.base_url}/v1/wallets/mpesa/get/all"
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                headers = await self._auth_headers()
                response = await client.post(
                    endpoint,
                    json={"client_id": self.client_id},
                    headers=headers,
                )
            return response.json() if response.status_code == 200 else None
        except Exception as exc:
            logger.error(f"E2Payments list_wallets: {exc}")
            return None
