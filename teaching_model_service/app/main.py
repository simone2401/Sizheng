from __future__ import annotations

import json
import os
from collections.abc import AsyncIterator

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import ValidationError

from .models import ErrorInfo, TeachingChatRequest, TeachingResponse
from .resources import InvalidResourceQuery, ResourceNotFound, ResourceQueryService
from .service import InputSafetyError, ModelClientError, TeachingChatService

app = FastAPI(title="Teaching Model Service", version="1.2.0")
resources = ResourceQueryService()
teaching_service = TeachingChatService(resources)


def _authorized(request: Request) -> bool:
    configured = {key.strip() for key in os.getenv("TEACHING_API_KEYS", "").split(",") if key.strip()}
    if not configured:
        return True
    value = request.headers.get("Authorization", "")
    scheme, _, token = value.partition(" ")
    return scheme.lower() == "bearer" and token in configured


def error_payload(request_id: str | None, conversation_id: str | None, turn_id: int, code: str, message: str, status: int, retriable: bool = False) -> JSONResponse:
    response = TeachingResponse(requestId=request_id or "", conversationId=conversation_id or "", turnId=turn_id, model=None, l1_labels=[], reasoning_content="", content="", finishReason="error", usage=None, error=ErrorInfo(code=code, message=message, retriable=retriable))
    return JSONResponse(status_code=status, content=response.model_dump(by_alias=True))


@app.get("/v1/teaching/resources")
def get_resources(request: Request, schoolLevel: str = Query(...), subject: str = Query(...), textbookVersion: str = Query(...), chapter: str = Query(...), lesson: str = Query(...), knowledgePoints: list[str] | None = Query(default=None)):
    if not _authorized(request):
        raise HTTPException(status_code=401, detail="unauthorized")
    try:
        return resources.query(schoolLevel, subject, textbookVersion, chapter, lesson, knowledgePoints)
    except ResourceNotFound as exc:
        raise HTTPException(status_code=404, detail={"code": "RESOURCE_NOT_FOUND", "message": str(exc), "retriable": False}) from exc
    except InvalidResourceQuery as exc:
        raise HTTPException(status_code=400, detail={"code": "INVALID_ARGUMENT", "message": str(exc), "retriable": False}) from exc


@app.post("/v1/chat/teaching")
async def teaching_chat(request: Request):
    if not _authorized(request):
        return error_payload(None, None, 1, "UNAUTHORIZED", "invalid teaching API key", 401)
    try:
        chat_request = TeachingChatRequest.model_validate(await request.json())
    except (json.JSONDecodeError, ValidationError) as exc:
        return error_payload(None, None, 1, "INVALID_ARGUMENT", str(exc), 400)
    try:
        if chat_request.stream:
            teaching_service.prepare(chat_request)
            return StreamingResponse(_sse_stream(chat_request), media_type="text/event-stream", headers={"Cache-Control": "no-cache", "Connection": "keep-alive"})
        return teaching_service.generate(chat_request).model_dump(by_alias=True)
    except ResourceNotFound as exc:
        return error_payload(chat_request.request_id, chat_request.conversation_id, chat_request.turn_id, "RESOURCE_NOT_FOUND", str(exc), 404)
    except InputSafetyError as exc:
        return error_payload(chat_request.request_id, chat_request.conversation_id, chat_request.turn_id, "SAFETY_BLOCK", str(exc), 400)
    except ModelClientError as exc:
        return error_payload(chat_request.request_id, chat_request.conversation_id, chat_request.turn_id, exc.code, str(exc), 502 if exc.code != "MODEL_RATE_LIMITED" else 429, exc.retriable)


async def _sse_stream(chat_request: TeachingChatRequest) -> AsyncIterator[str]:
    try:
        for response in teaching_service.stream_chunks(chat_request):
            yield f"event: message\ndata: {json.dumps(response.model_dump(by_alias=True), ensure_ascii=False)}\n\n"
    except (ResourceNotFound, InputSafetyError, ModelClientError) as exc:
        code = getattr(exc, "code", "SAFETY_BLOCK" if isinstance(exc, InputSafetyError) else "RESOURCE_NOT_FOUND")
        yield _sse_error(chat_request, code, str(exc), getattr(exc, "retriable", False))


def _sse_error(request: TeachingChatRequest, code: str, message: str, retriable: bool = False) -> str:
    response = TeachingResponse(requestId=request.request_id or "", conversationId=request.conversation_id or "", turnId=request.turn_id, model=None, l1_labels=[], reasoning_content="", content="", finishReason="error", usage=None, error=ErrorInfo(code=code, message=message, retriable=retriable))
    return f"event: message\ndata: {json.dumps(response.model_dump(by_alias=True), ensure_ascii=False)}\n\n"
