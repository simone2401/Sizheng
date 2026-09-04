from __future__ import annotations
import json
from fastapi import APIRouter, Depends, Header, Request
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import ValidationError
from app.shared.auth import authorized
from app.shared.config import ModelSettings
from app.shared.errors import ServiceError, UnauthorizedError, error_dict
from .models import ErrorInfo, TeachingChatRequest, TeachingResponse
from .sse import encode
from .teaching_service import TeachingChatService, PreparedTeachingRequest
router = APIRouter()

def service_dependency() -> TeachingChatService: raise RuntimeError("teaching service is not initialized")
def settings_dependency() -> ModelSettings: return ModelSettings.from_env()

def error_payload(req, error: ServiceError):
    response = TeachingResponse(requestId=getattr(req, "request_id", "") or "", conversationId=getattr(req, "conversation_id", "") or "", turnId=getattr(req, "turn_id", 1), model=None, finishReason="error", error=ErrorInfo(**error_dict(error)))
    return JSONResponse(status_code=error.status_code, content=response.model_dump(by_alias=True))

@router.post("/v1/chat/teaching")
async def teaching_chat(request: Request, authorization: str | None = Header(None), service: TeachingChatService = Depends(service_dependency), settings: ModelSettings = Depends(settings_dependency)):
    if not authorized(authorization, settings.api_keys, settings.auth_disabled): return error_payload(None, UnauthorizedError())
    try: chat = TeachingChatRequest.model_validate(await request.json())
    except (json.JSONDecodeError, ValidationError) as exc: return error_payload(None, ServiceError("INVALID_ARGUMENT", str(exc), 400))
    try: prepared = await service.prepare(chat)
    except ServiceError as exc: return error_payload(chat, exc)
    if not chat.stream:
        try: return (await service.generate(prepared)).model_dump(by_alias=True)
        except ServiceError as exc: return error_payload(chat, exc)
    async def stream():
        try:
            async for item in service.stream(prepared): yield encode(item)
        except ServiceError as exc: yield encode(TeachingResponse(requestId=chat.request_id or "", conversationId=chat.conversation_id or "", turnId=chat.turn_id, model=None, finishReason="error", error=ErrorInfo(**error_dict(exc))))
    return StreamingResponse(stream(), media_type="text/event-stream", headers={"Cache-Control":"no-cache", "Connection":"keep-alive"})
