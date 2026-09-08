from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.modules.recharges.infrastructure.repositories.recharge_repository import SQLAlchemyRechargeRepository
from app.modules.meters.infrastructure.repositories.meter_repository import SQLAlchemyMeterRepository
from app.modules.recharges.application.usecases.recharge_service import (
    InitiateRechargeUseCase,
    GetRechargeStatusUseCase,
    GetRechargeHistoryUseCase,
    GetRechargeDashboardUseCase,
)
from app.modules.recharges.application.usecases.manual_code import ApplyManualCodeUseCase

from app.modules.recharges.application.usecases.admin_transactions import ListAdminTransactionsUseCase
from app.modules.audit.presentation.dependencies import get_create_audit_log_usecase
from app.modules.audit.application.usecases.create_audit_log import CreateAuditLogUseCase


def get_recharge_repository(db: Session = Depends(get_db)):
    return SQLAlchemyRechargeRepository(db)


def get_meter_repository(db: Session = Depends(get_db)):
    return SQLAlchemyMeterRepository(db)


def get_initiate_recharge_usecase(
    recharge_repo: SQLAlchemyRechargeRepository = Depends(get_recharge_repository),
    meter_repo: SQLAlchemyMeterRepository = Depends(get_meter_repository),
    db: Session = Depends(get_db),
    audit_usecase: CreateAuditLogUseCase = Depends(get_create_audit_log_usecase),
):
    return InitiateRechargeUseCase(recharge_repo, meter_repo, db, audit_usecase)


def get_recharge_status_usecase(
    recharge_repo: SQLAlchemyRechargeRepository = Depends(get_recharge_repository),
    meter_repo: SQLAlchemyMeterRepository = Depends(get_meter_repository),
):
    return GetRechargeStatusUseCase(recharge_repo, meter_repo)


def get_recharge_history_usecase(
    recharge_repo: SQLAlchemyRechargeRepository = Depends(get_recharge_repository),
):
    return GetRechargeHistoryUseCase(recharge_repo)


def get_recharge_dashboard_usecase(
    recharge_repo: SQLAlchemyRechargeRepository = Depends(get_recharge_repository),
):
    return GetRechargeDashboardUseCase(recharge_repo)


def get_apply_manual_code_usecase(
    recharge_repo: SQLAlchemyRechargeRepository = Depends(get_recharge_repository),
    meter_repo: SQLAlchemyMeterRepository = Depends(get_meter_repository),
):
    return ApplyManualCodeUseCase(recharge_repo, meter_repo)

def get_list_admin_transactions_usecase(
    recharge_repo: SQLAlchemyRechargeRepository = Depends(get_recharge_repository)
):
    return ListAdminTransactionsUseCase(recharge_repo)

def get_admin_generate_token_usecase(
    recharge_repo: SQLAlchemyRechargeRepository = Depends(get_recharge_repository),
    meter_repo: SQLAlchemyMeterRepository = Depends(get_meter_repository),
):
    from app.modules.recharges.application.usecases.admin_generate_token import AdminGenerateTokenUseCase
    return AdminGenerateTokenUseCase(recharge_repo, meter_repo)
