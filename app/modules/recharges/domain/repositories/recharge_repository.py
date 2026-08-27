import uuid
from abc import ABC, abstractmethod
from typing import List, Optional
from datetime import datetime

from app.modules.recharges.domain.entities.recharge import Recarga
from app.modules.recharges.domain.entities.schemas import RechargeInitiateRequest


class IRechargeRepository(ABC):

    @abstractmethod
    def create(self, user_id: uuid.UUID, meter_id: uuid.UUID, data: RechargeInitiateRequest) -> Recarga:
        """Cria uma nova recarga com estado PENDING."""
        ...

    @abstractmethod
    def get_by_id(self, recharge_id: uuid.UUID) -> Optional[Recarga]:
        """Devolve uma recarga pelo seu ID."""
        ...

    @abstractmethod
    def get_by_meter_and_code(self, recharge_code: str) -> Optional[Recarga]:
        """Verifica se um código manual já foi utilizado (RN10 — idempotência)."""
        ...

    @abstractmethod
    def get_history(
        self,
        user_id: uuid.UUID,
        meter_id: Optional[uuid.UUID] = None,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
        skip: int = 0,
        limit: int = 20,
    ) -> tuple[List[Recarga], int]:
        """Devolve histórico paginado e total de registos."""
        ...

    @abstractmethod
    def update_status(self, recharge_id: uuid.UUID, new_status: str) -> Optional[Recarga]:
        """Actualiza o estado de uma recarga."""
        ...

    @abstractmethod
    def update_token(self, recharge_id: uuid.UUID, token: str, applied_at: datetime) -> Optional[Recarga]:
        """Grava o token STS gerado e o timestamp de aplicação."""
        ...

    @abstractmethod
    def get_dashboard_stats(
        self,
        user_id: uuid.UUID,
        meter_id: Optional[uuid.UUID] = None,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
    ) -> dict:
        """Agrega estatísticas de consumo para o dashboard."""
        ...
