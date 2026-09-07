from contextlib import asynccontextmanager
import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from app.core.config import settings
from app.core.mqtt import start_mqtt, stop_mqtt
from app.core.router import api_router
from app.core.reconciliation import reconciliation_task

logging.basicConfig(level=logging.INFO)
logging.getLogger("httpx").setLevel(logging.WARNING)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    start_mqtt()
    task = asyncio.create_task(reconciliation_task())
    yield
    # Shutdown
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass
    stop_mqtt()

app = FastAPI(
    title="Gezi Backend API",
    description="Backend FastAPI para a Plataforma Gezi",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/v1")

@app.get("/health", tags=["System"])
def health_check():
    return {
        "status": "healthy",
        "environment": settings.environment,
        "service": "Gezi API"
    }
