import uuid
import asyncio
import json
from datetime import datetime
from typing import Optional, Dict, Any

from fastapi import APIRouter, Depends, Query
from starlette.responses import StreamingResponse

from app.core.event_bus import event_bus
from app.modules.auth.presentation.dependencies import get_current_user
from app.modules.auth.domain.entities.auth import AuthUser
from app.modules.recharges.domain.entities.schemas import (
    RechargeInitiateRequest,
    ManualCodeRequest,
)
from app.modules.recharges.presentation.dependencies import (
    get_initiate_recharge_usecase,
    get_recharge_status_usecase,
    get_recharge_history_usecase,
    get_recharge_dashboard_usecase,
    get_apply_manual_code_usecase,
)
from app.modules.recharges.application.usecases.recharge_service import (
    InitiateRechargeUseCase,
    GetRechargeStatusUseCase,
    GetRechargeHistoryUseCase,
    GetRechargeDashboardUseCase,
)
from app.modules.recharges.application.usecases.manual_code import ApplyManualCodeUseCase

router = APIRouter()


@router.post("/initiate", status_code=201)
def initiate_recharge(
    data: RechargeInitiateRequest,
    current_user: AuthUser = Depends(get_current_user),
    usecase: InitiateRechargeUseCase = Depends(get_initiate_recharge_usecase),
) -> Dict[str, Any]:
    """
    RF03 — Inicia o processo de recarga (cria registo PENDING antes do pagamento).
    """
    result = usecase.execute(current_user.id, data)
    return {
        "success": True,
        "data": result.model_dump(),
        "error": None,
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }


@router.get("/{recharge_id}/status")
def get_recharge_status(
    recharge_id: uuid.UUID,
    current_user: AuthUser = Depends(get_current_user),
    usecase: GetRechargeStatusUseCase = Depends(get_recharge_status_usecase),
) -> Dict[str, Any]:
    """RF03 — Consulta o estado actual de uma recarga (one-shot)."""
    result = usecase.execute(current_user.id, recharge_id)
    return {
        "success": True,
        "data": result.model_dump(),
        "error": None,
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }


@router.get("/{recharge_id}/stream")
async def stream_recharge_status(
    recharge_id: uuid.UUID,
    current_user: AuthUser = Depends(get_current_user),
    usecase: GetRechargeStatusUseCase = Depends(get_recharge_status_usecase),
):
    """
    SSE — Stream de eventos em tempo real para acompanhar o estado de uma recarga.

    O Flutter conecta a este endpoint apos iniciar uma recarga e recebe eventos
    automaticamente sempre que o estado muda (CONFIRMED, MQTT_SENT, CONCLUIDA).

    Content-Type: text/event-stream
    """
    # Verificar que a recarga pertence ao utilizador (one-shot check)
    result = usecase.execute(current_user.id, recharge_id)

    async def event_generator():
        recharge_key = str(recharge_id)
        queue = event_bus.subscribe(recharge_key)

        try:
            # Enviar estado actual como primeiro evento
            initial_event = {
                "event": "status_update",
                "data": result.model_dump(),
            }
            yield f"data: {json.dumps(initial_event, default=str)}\n\n"

            # Se ja esta concluida, nao ha nada para esperar
            if result.status in ("CONCLUIDA", "FAILED", "REFUNDED"):
                yield f"data: {json.dumps({'event': 'stream_end'})}\n\n"
                return

            # Escutar eventos do event bus
            while True:
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=30.0)
                    yield f"data: {json.dumps(event, default=str)}\n\n"

                    # Fechar stream se recarga terminou
                    status_data = event.get("data", {})
                    if status_data.get("status") in ("CONCLUIDA", "FAILED", "REFUNDED"):
                        yield f"data: {json.dumps({'event': 'stream_end'})}\n\n"
                        return
                except asyncio.TimeoutError:
                    # Heartbeat para manter a conexao viva
                    yield ": heartbeat\n\n"
        finally:
            event_bus.unsubscribe(recharge_key, queue)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/manual-code")
def apply_manual_code(
    data: ManualCodeRequest,
    current_user: AuthUser = Depends(get_current_user),
    usecase: ApplyManualCodeUseCase = Depends(get_apply_manual_code_usecase),
) -> Dict[str, Any]:
    """
    RF16, RN10 — Aplica um código de recarga CREDELEC obtido por canal externo.
    Retorna 409 se o código já foi utilizado anteriormente.
    """
    result = usecase.execute(current_user.id, data)
    return {
        "success": True,
        "data": result.model_dump(),
        "error": None,
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }


@router.get("/history")
def get_recharge_history(
    meter_id: Optional[uuid.UUID] = Query(None, description="Filtrar por contador"),
    from_date: Optional[datetime] = Query(None, alias="from", description="Data início (ISO 8601)"),
    to_date: Optional[datetime] = Query(None, alias="to", description="Data fim (ISO 8601)"),
    page: int = Query(1, ge=1, description="Número da página"),
    page_size: int = Query(20, ge=1, le=100, description="Itens por página"),
    current_user: AuthUser = Depends(get_current_user),
    usecase: GetRechargeHistoryUseCase = Depends(get_recharge_history_usecase),
) -> Dict[str, Any]:
    """RF06 — Histórico de recargas com filtros e paginação."""
    result = usecase.execute(
        user_id=current_user.id,
        meter_id=meter_id,
        from_date=from_date,
        to_date=to_date,
        page=page,
        page_size=page_size,
    )
    return {
        "success": True,
        "data": result.model_dump(),
        "error": None,
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }


@router.get("/dashboard")
def get_recharge_dashboard(
    meter_id: Optional[uuid.UUID] = Query(None, description="Filtrar por contador"),
    period: Optional[str] = Query("month", description="Período: week | month | year"),
    current_user: AuthUser = Depends(get_current_user),
    usecase: GetRechargeDashboardUseCase = Depends(get_recharge_dashboard_usecase),
) -> Dict[str, Any]:
    """RF14 — Estatísticas agregadas de consumo."""
    # Calcular datas com base no período
    from datetime import timedelta
    now = datetime.utcnow()
    period_map = {
        "week": timedelta(days=7),
        "month": timedelta(days=30),
        "year": timedelta(days=365),
    }
    delta = period_map.get(period, timedelta(days=30))
    from_date = now - delta

    result = usecase.execute(
        user_id=current_user.id,
        meter_id=meter_id,
        from_date=from_date,
        to_date=now,
    )
    return {
        "success": True,
        "data": result.model_dump(),
        "error": None,
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }
