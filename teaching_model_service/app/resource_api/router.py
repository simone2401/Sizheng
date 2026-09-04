from __future__ import annotations

from typing import Any
from fastapi import APIRouter, Depends, Header, HTTPException, Query
from pydantic import ValidationError
from app.shared.auth import authorized
from app.shared.config import ResourceSettings
from app.shared.errors import InvalidArgumentError, ResourceNotFoundError, UnauthorizedError, error_dict
from app.shared.resource_contracts import ResourceQuery, ResourceResponse
from .service import ResourceService

router = APIRouter()


def service_dependency() -> ResourceService:
    raise RuntimeError("resource service is not initialized")


def settings_dependency() -> ResourceSettings:
    return ResourceSettings.from_env()


@router.get("/v1/teaching/resources", response_model=ResourceResponse)
def get_resources(
    school_level: str = Query(..., alias="schoolLevel", min_length=1),
    subject: str = Query(..., min_length=1),
    textbook_version: str = Query(..., alias="textbookVersion", min_length=1),
    chapter: str = Query(..., min_length=1),
    lesson: str = Query(..., min_length=1),
    knowledge_points: list[str] | None = Query(None, alias="knowledgePoints"),
    authorization: str | None = Header(None),
    service: ResourceService = Depends(service_dependency),
    settings: ResourceSettings = Depends(settings_dependency),
) -> ResourceResponse:
    if not authorized(authorization, settings.api_keys, settings.auth_disabled):
        raise HTTPException(401, detail=error_dict(UnauthorizedError()))
    try:
        query = ResourceQuery(
            schoolLevel=school_level,
            subject=subject,
            textbookVersion=textbook_version,
            chapter=chapter,
            lesson=lesson,
            knowledgePoints=knowledge_points,
        )
        return service.query(query)
    except ResourceNotFoundError as exc:
        raise HTTPException(exc.status_code, detail=error_dict(exc)) from exc
    except ValidationError as exc:
        raise HTTPException(400, detail=error_dict(InvalidArgumentError(str(exc)))) from exc
