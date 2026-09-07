from fastapi import Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.modules.iot.infrastructure.repositories.iot_repository import SQLAlchemyIoTRepository
from app.modules.iot.application.usecases.list_iot_devices import ListIoTDevicesUseCase

def get_iot_repository(db: Session = Depends(get_db)):
    return SQLAlchemyIoTRepository(db)

def get_list_iot_devices_usecase(repo: SQLAlchemyIoTRepository = Depends(get_iot_repository)):
    return ListIoTDevicesUseCase(repo)
