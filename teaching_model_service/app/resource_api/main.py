from __future__ import annotations

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.shared.config import ResourceSettings
from .repository import ResourceRepository
from .router import router, service_dependency
from .service import ResourceService


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = ResourceSettings.from_env()
    repository = ResourceRepository(settings.resource_dir)
    try:
        repository.load()
        app.state.resource_service = ResourceService(repository)
        app.state.resource_error = None
    except Exception as exc:
        app.state.resource_error = exc
    yield


app = FastAPI(title="Teaching Resource API", version="1.0.0", lifespan=lifespan)
_resource_settings = ResourceSettings.from_env()
app.add_middleware(
    CORSMiddleware,
    allow_origins=list(_resource_settings.cors_allow_origins),
    allow_credentials=False,
    allow_methods=["GET", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)
app.include_router(router)


def current_service() -> ResourceService:
    service = getattr(app.state, "resource_service", None)
    if service is None:
        raise RuntimeError("resource service is not ready")
    return service


app.dependency_overrides[service_dependency] = current_service


@app.get("/health/live")
def live() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/health/ready")
def ready() -> dict[str, object]:
    if getattr(app.state, "resource_error", None) is not None:
        return {"status": "unavailable", "ready": False}
    return {"status": "ok", "ready": hasattr(app.state, "resource_service")}
