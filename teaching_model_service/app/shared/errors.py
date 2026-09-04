from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ServiceError(Exception):
    code: str
    message: str
    status_code: int = 500
    retriable: bool = False

    def __str__(self) -> str:
        return self.message


class UnauthorizedError(ServiceError):
    def __init__(self, message: str = "invalid API key") -> None:
        super().__init__("UNAUTHORIZED", message, 401, False)


class InvalidArgumentError(ServiceError):
    def __init__(self, message: str) -> None:
        super().__init__("INVALID_ARGUMENT", message, 400, False)


class ResourceNotFoundError(ServiceError):
    def __init__(self, message: str = "resource not found") -> None:
        super().__init__("RESOURCE_NOT_FOUND", message, 404, False)


class ResourceUnavailableError(ServiceError):
    def __init__(self, message: str = "resource service unavailable") -> None:
        super().__init__("RESOURCE_SERVICE_UNAVAILABLE", message, 503, True)


class ModelClientError(ServiceError):
    pass


class SafetyError(ServiceError):
    def __init__(self, message: str) -> None:
        super().__init__("SAFETY_BLOCK", message, 400, False)


def error_dict(error: ServiceError) -> dict[str, object]:
    return {"code": error.code, "message": error.message, "retriable": error.retriable}
