from fastapi import APIRouter

api_router = APIRouter()

@api_router.get("/status")
def api_status():
    return {"status": "v1 API is working"}

# TODO: Import and include domain routers
# from app.api.v1.endpoints import auth, meter, recharge, payment, iot, admin, documents
# api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
