from app.modules.iot.infrastructure.repositories.iot_repository import SQLAlchemyIoTRepository
from app.modules.iot.domain.entities.schemas import IoTAdminDeviceListResponse, IoTAdminDeviceResponse
import uuid

class ListIoTDevicesUseCase:
    def __init__(self, iot_repo: SQLAlchemyIoTRepository):
        self.iot_repo = iot_repo

    def execute(self, skip: int = 0, limit: int = 100) -> IoTAdminDeviceListResponse:
        results, total = self.iot_repo.get_all_devices(skip=skip, limit=limit)
        
        devices = [IoTAdminDeviceResponse.model_validate(r) for r in results]
        return IoTAdminDeviceListResponse(
            devices=devices,
            total=total
        )
