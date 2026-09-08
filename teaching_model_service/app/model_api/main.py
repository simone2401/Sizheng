from __future__ import annotations

from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.shared.config import ModelSettings
from .model_clients import MockModelClient, ZhipuModelClient
from .resource_client import ResourceClient
from .router import router, service_dependency, settings_dependency
from .teaching_service import TeachingChatService


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = app.state.bootstrap_settings
    app.state.settings = settings
    async with httpx.AsyncClient(timeout=settings.model_timeout) as client:
        app.state.resource_client = ResourceClient(settings, client)
        model_client = (
            ZhipuModelClient(
                settings.zhipu_api_key,
                settings.zhipu_model,
                settings.model_timeout,
                base_url=settings.zhipu_base_url,
                client=client,
            )
            if settings.model_backend == "zhipu"
            else MockModelClient()
        )
        app.state.teaching_service = TeachingChatService(
            app.state.resource_client, model_client=model_client, settings=settings
        )
        app.state.ready = settings.ready
        yield

def create_app() -> FastAPI:
    settings = ModelSettings.from_env()
    application = FastAPI(title="Teaching Model API", version="1.0.0", lifespan=lifespan)
    application.state.bootstrap_settings = settings
    application.add_middleware(
        CORSMiddleware,
        allow_origins=list(settings.cors_allow_origins),
        allow_credentials=False,
        allow_methods=["POST", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type"],
    )
    application.include_router(router)
    return application


app = create_app()


def current_service() -> TeachingChatService:
    service = getattr(app.state, "teaching_service", None)
    if service is None:
        raise RuntimeError("teaching service is not initialized")
    return service


def current_settings() -> ModelSettings:
    settings = getattr(app.state, "settings", None)
    if settings is None:
        raise RuntimeError("model settings are not initialized")
    return settings


app.dependency_overrides[service_dependency] = current_service
app.dependency_overrides[settings_dependency] = current_settings


@app.get("/health/live")
def live():
    return {"status": "ok"}


@app.get("/health/ready")
def ready():
    if not getattr(app.state, "ready", False):
        return JSONResponse(status_code=503, content={"status": "unavailable", "ready": False})
    return {"status": "ok", "ready": True}
