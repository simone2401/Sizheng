from __future__ import annotations
from contextlib import asynccontextmanager
import httpx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.shared.config import ModelSettings
from .resource_client import ResourceClient
from .router import router, service_dependency
from .teaching_service import TeachingChatService

@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = ModelSettings.from_env()
    async with httpx.AsyncClient(timeout=settings.model_timeout) as client:
        app.state.resource_client = ResourceClient(settings, client)
        app.state.teaching_service = TeachingChatService(app.state.resource_client, settings=settings)
        app.state.ready = settings.ready
        yield

app = FastAPI(title="Teaching Model API", version="1.0.0", lifespan=lifespan)
_model_settings = ModelSettings.from_env()
app.add_middleware(
    CORSMiddleware,
    allow_origins=list(_model_settings.cors_allow_origins),
    allow_credentials=False,
    allow_methods=["POST", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)
app.include_router(router)

def current_service() -> TeachingChatService:
    return app.state.teaching_service
app.dependency_overrides[service_dependency] = current_service

@app.get("/health/live")
def live(): return {"status": "ok"}
@app.get("/health/ready")
def ready(): return {"status": "ok", "ready": bool(getattr(app.state, "ready", False))} if getattr(app.state, "ready", False) else {"status": "unavailable", "ready": False}
