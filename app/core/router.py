from fastapi import APIRouter

api_router = APIRouter()

@api_router.get("/status")
def api_status():
    return {"status": "v1 API is working"}

from app.modules.auth.presentation.controllers import auth
from app.modules.users.presentation.controllers import user as user_controller, admin as user_admin
from app.modules.meters.presentation.controllers import meter as meter_controller, admin as meter_admin
from app.modules.recharges.presentation.controllers import recharge as recharge_controller
from app.modules.iot.presentation.controllers import iot as iot_controller
from app.modules.payments.presentation.controllers import payment as payment_controller

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(user_controller.router, prefix="/users", tags=["users"])
api_router.include_router(user_admin.router, prefix="/admin", tags=["admin"])
api_router.include_router(meter_controller.router, prefix="/meters", tags=["meters"])
api_router.include_router(meter_admin.router, prefix="/admin", tags=["admin"])
api_router.include_router(recharge_controller.router, prefix="/recharges", tags=["recharges"])
api_router.include_router(iot_controller.router, prefix="/iot", tags=["iot"])
api_router.include_router(payment_controller.router, prefix="/payments", tags=["payments"])


