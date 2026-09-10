from fastapi import Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.modules.meters.infrastructure.repositories.meter_repository import SQLAlchemyMeterRepository
from app.modules.meters.application.usecases.register_meter import RegisterMeterUseCase
from app.modules.meters.application.usecases.list_my_meters import ListMyMetersUseCase
from app.modules.meters.application.usecases.get_meter import GetMeterUseCase
from app.modules.meters.application.usecases.update_meter import UpdateMeterUseCase
from app.modules.meters.application.usecases.get_meter_status import GetMeterStatusUseCase
from app.modules.meters.application.usecases.list_all_meters import ListAllMetersUseCase
from app.modules.meters.application.usecases.list_all_meters_detailed import ListAllMetersDetailedUseCase
from app.modules.meters.application.usecases.admin_update_meter import AdminUpdateMeterUseCase
from app.modules.meters.application.usecases.admin_create_meter import AdminCreateMeterUseCase
from app.modules.audit.presentation.dependencies import get_create_audit_log_usecase
from app.modules.audit.application.usecases.create_audit_log import CreateAuditLogUseCase
from app.modules.meters.application.usecases.lookup_meter import LookupMeterUseCase

def get_meter_repository(db: Session = Depends(get_db)):
    return SQLAlchemyMeterRepository(db)

def get_register_meter_usecase(repo: SQLAlchemyMeterRepository = Depends(get_meter_repository)):
    return RegisterMeterUseCase(repo)

def get_list_my_meters_usecase(repo: SQLAlchemyMeterRepository = Depends(get_meter_repository)):
    return ListMyMetersUseCase(repo)

def get_get_meter_usecase(repo: SQLAlchemyMeterRepository = Depends(get_meter_repository)):
    return GetMeterUseCase(repo)

def get_lookup_meter_usecase(repo: SQLAlchemyMeterRepository = Depends(get_meter_repository)):
    return LookupMeterUseCase(repo)

def get_update_meter_usecase(repo: SQLAlchemyMeterRepository = Depends(get_meter_repository)):
    return UpdateMeterUseCase(repo)

def get_get_meter_status_usecase(repo: SQLAlchemyMeterRepository = Depends(get_meter_repository)):
    return GetMeterStatusUseCase(repo)

def get_list_all_meters_usecase(repo: SQLAlchemyMeterRepository = Depends(get_meter_repository)):
    return ListAllMetersUseCase(repo)

def get_list_all_meters_detailed_usecase(repo: SQLAlchemyMeterRepository = Depends(get_meter_repository)):
    return ListAllMetersDetailedUseCase(repo)

def get_admin_update_meter_usecase(
    repo: SQLAlchemyMeterRepository = Depends(get_meter_repository),
    audit_usecase: CreateAuditLogUseCase = Depends(get_create_audit_log_usecase)
):
    return AdminUpdateMeterUseCase(repo, audit_usecase)

def get_admin_create_meter_usecase(repo: SQLAlchemyMeterRepository = Depends(get_meter_repository)):
    return AdminCreateMeterUseCase(repo)

def get_revoke_meter_access_usecase(
    repo: SQLAlchemyMeterRepository = Depends(get_meter_repository),
    audit_usecase: CreateAuditLogUseCase = Depends(get_create_audit_log_usecase)
):
    from app.modules.meters.application.usecases.revoke_meter_access import RevokeMeterAccessUseCase
    return RevokeMeterAccessUseCase(repo, audit_usecase)
