"""
IPaymentGateway — Interface do gateway de pagamento.

Desacopla os use cases de qualquer gateway concreto (E2Payments, Mpesa directo, etc.).
Se o gateway mudar no futuro, apenas o provider de infraestrutura é substituído.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class PaymentGatewayResult:
    """Resultado de uma tentativa de iniciar um pagamento C2B."""
    success: bool
    gateway_reference: Optional[str] = None  # referencia interna do gateway
    raw_response: Optional[dict] = None
    error_message: Optional[str] = None


@dataclass
class PaymentStatusResult:
    """Resultado de uma consulta de estado de pagamento no gateway."""
    reference: str          # referencia que identifica o pagamento no nosso sistema
    confirmed: bool         # True se o gateway confirmou o pagamento
    amount: Optional[float] = None
    phone: Optional[str] = None
    gateway_data: Optional[dict] = None


class IPaymentGateway(ABC):
    """
    Interface abstracta para gateway de pagamento M-Pesa/eMola.
    Todos os providers de infraestrutura devem implementar esta interface.
    """

    @abstractmethod
    async def initiate_c2b(
        self,
        amount: float,
        phone: str,
        reference: str,
    ) -> PaymentGatewayResult:
        """
        Inicia uma transacção C2B (Customer to Business).
        Dispara o STK Push no telemóvel do cliente.

        Args:
            amount:    Montante em MZN.
            phone:     Número de telefone do cliente (9 dígitos, sem código de país).
            reference: Referência única da transacção (sem espaços, ex: GEZI-abc123).

        Returns:
            PaymentGatewayResult com sucesso ou erro.
        """
        ...

    @abstractmethod
    async def get_recent_confirmed_payments(
        self, limit: int = 20
    ) -> list[PaymentStatusResult]:
        """
        Obtém os pagamentos confirmados mais recentes do gateway.
        Usado para reconciliação por polling (não há webhooks no E2Payments).

        Args:
            limit: Número máximo de pagamentos a consultar.

        Returns:
            Lista de PaymentStatusResult para os pagamentos confirmados.
        """
        ...
