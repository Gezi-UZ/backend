from fastapi import APIRouter

api_router = APIRouter()

@api_router.get("/status")
def api_status():
    return {"status": "v1 API is working"}

from app.modules.auth.presentation.controllers import auth
from app.modules.users.presentation.controllers import user, admin

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(user.router, prefix="/users", tags=["users"])
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])
