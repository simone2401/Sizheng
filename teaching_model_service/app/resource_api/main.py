from __future__ import annotations

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.shared.config import ResourceSettings
from app.shared.errors import ResourceUnavailableError, error_dict
from .repository import ResourceRepository
from .router import router, service_dependency, settings_dependency
from .service import ResourceService


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = app.state.bootstrap_settings
    app.state.settings = settings
    repository = ResourceRepository(settings.resource_dir)
    try:
        repository.load()
        app.state.resource_service = ResourceService(repository)
        app.state.resource_error = None
    except Exception as exc:
        app.state.resource_error = exc
    yield

def create_app() -> FastAPI:
    settings = ResourceSettings.from_env()
    application = FastAPI(title="Teaching Resource API", version="1.0.0", lifespan=lifespan)
    application.state.bootstrap_settings = settings
    origins = list(settings.cors_allow_origins)
    if "null" not in origins:
        origins.append("null")
    if not settings.cors_allow_origins:
        origins = ["*"]
    application.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=False,
        allow_methods=["GET", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type"],
    )
    application.include_router(router)
    return application


app = create_app()


@app.exception_handler(ResourceUnavailableError)
def resource_unavailable(_: Request, exc: ResourceUnavailableError) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content={"detail": error_dict(exc)})


def current_service() -> ResourceService:
    service = getattr(app.state, "resource_service", None)
    if service is None:
        raise ResourceUnavailableError() from getattr(app.state, "resource_error", None)
    return service


def current_settings() -> ResourceSettings:
    settings = getattr(app.state, "settings", None)
    if settings is None:
        raise RuntimeError("resource settings are not initialized")
    return settings


app.dependency_overrides[service_dependency] = current_service
app.dependency_overrides[settings_dependency] = current_settings


@app.get("/health/live")
def live() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/health/ready")
def ready():
    if getattr(app.state, "resource_error", None) is not None:
        return JSONResponse(status_code=503, content={"status": "unavailable", "ready": False})
    return {"status": "ok", "ready": hasattr(app.state, "resource_service")}
