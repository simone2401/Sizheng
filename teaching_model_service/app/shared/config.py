from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def _keys(name: str) -> frozenset[str]:
    return frozenset(value.strip() for value in os.getenv(name, "").split(",") if value.strip())


def _bool(name: str, default: bool = False) -> bool:
    return os.getenv(name, str(default)).strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class ResourceSettings:
    host: str
    port: int
    resource_dir: str | None
    api_keys: frozenset[str]
    auth_disabled: bool
    cors_allow_origins: tuple[str, ...]
    @classmethod
    def from_env(cls) -> "ResourceSettings":
        return cls(
            os.getenv("RESOURCE_API_HOST", "127.0.0.1"),
            int(os.getenv("RESOURCE_API_PORT", "8001")),
            os.getenv("TEACHING_RESOURCE_DIR") or str(default_resource_dir()),
            _keys("RESOURCE_API_KEYS"),
            _bool("RESOURCE_API_AUTH_DISABLED"),
            tuple(value.strip() for value in os.getenv("CORS_ALLOW_ORIGINS", "").split(",") if value.strip()),
        )


@dataclass(frozen=True)
class ModelSettings:
    host: str
    port: int
    resource_service_url: str
    resource_service_api_key: str
    api_keys: frozenset[str]
    auth_disabled: bool
    model_backend: str
    zhipu_api_key: str
    zhipu_base_url: str
    zhipu_model: str
    model_timeout: float
    cors_allow_origins: tuple[str, ...]

    @classmethod
    def from_env(cls) -> "ModelSettings":
        return cls(
            os.getenv("MODEL_API_HOST", "127.0.0.1"),
            int(os.getenv("MODEL_API_PORT", "8000")),
            os.getenv("RESOURCE_SERVICE_URL", "http://127.0.0.1:8001").rstrip("/"),
            os.getenv("RESOURCE_SERVICE_API_KEY", ""),
            _keys("TEACHING_API_KEYS"),
            _bool("MODEL_API_AUTH_DISABLED"),
            os.getenv("MODEL_BACKEND", "mock").strip().lower(),
            os.getenv("ZHIPU_API_KEY", ""),
            os.getenv("ZHIPU_BASE_URL", "https://open.bigmodel.cn/api/paas/v4").rstrip("/"),
            os.getenv("ZHIPU_MODEL", "glm-5.2"),
            float(os.getenv("MODEL_TIMEOUT", "60")),
            tuple(value.strip() for value in os.getenv("CORS_ALLOW_ORIGINS", "").split(",") if value.strip()),
        )

    @property
    def ready(self) -> bool:
        return self.model_backend == "mock" or (self.model_backend == "zhipu" and bool(self.zhipu_api_key))


def default_resource_dir() -> Path:
    return Path(__file__).resolve().parents[3] / "json_output" / "PEP8U_PHYSICS"
