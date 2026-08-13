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

def get_meter_repository(db: Session = Depends(get_db)):
    return SQLAlchemyMeterRepository(db)

def get_register_meter_usecase(repo: SQLAlchemyMeterRepository = Depends(get_meter_repository)):
    return RegisterMeterUseCase(repo)

def get_list_my_meters_usecase(repo: SQLAlchemyMeterRepository = Depends(get_meter_repository)):
    return ListMyMetersUseCase(repo)

def get_get_meter_usecase(repo: SQLAlchemyMeterRepository = Depends(get_meter_repository)):
    return GetMeterUseCase(repo)

def get_update_meter_usecase(repo: SQLAlchemyMeterRepository = Depends(get_meter_repository)):
    return UpdateMeterUseCase(repo)

def get_get_meter_status_usecase(repo: SQLAlchemyMeterRepository = Depends(get_meter_repository)):
    return GetMeterStatusUseCase(repo)

def get_list_all_meters_usecase(repo: SQLAlchemyMeterRepository = Depends(get_meter_repository)):
    return ListAllMetersUseCase(repo)
