from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from app.core.config import settings
from app.core.mqtt import start_mqtt, stop_mqtt
from app.api.v1.router import api_router

logging.basicConfig(level=logging.INFO)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Ligar MQTT
    start_mqtt()
    yield
    # Shutdown: Desligar MQTT
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
