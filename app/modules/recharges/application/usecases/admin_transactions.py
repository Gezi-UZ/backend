from app.modules.recharges.infrastructure.repositories.recharge_repository import SQLAlchemyRechargeRepository
from app.modules.recharges.domain.entities.schemas import AdminTransactionListResponse, AdminTransactionResponse, PaginationMeta
import uuid
from typing import Optional
from datetime import datetime

class ListAdminTransactionsUseCase:
    def __init__(self, recharge_repo: SQLAlchemyRechargeRepository):
        self.recharge_repo = recharge_repo

    def execute(
        self,
        status: Optional[str] = None,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
        meter_id: Optional[uuid.UUID] = None,
        page: int = 1,
        page_size: int = 20
    ) -> AdminTransactionListResponse:
        skip = (page - 1) * page_size
        results, total = self.recharge_repo.get_all_admin(
            status=status,
            from_date=from_date,
            to_date=to_date,
            meter_id=meter_id,
            skip=skip,
            limit=page_size
        )
        
        transactions = [AdminTransactionResponse.model_validate(r) for r in results]
        
        return AdminTransactionListResponse(
            transactions=transactions,
            pagination=PaginationMeta(
                page=page,
                page_size=page_size,
                total=total
            )
        )
