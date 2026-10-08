from __future__ import annotations
import json
import asyncio
from fastapi import APIRouter, Depends, Header, Query, Request
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import ValidationError
from app.shared.auth import authorized
from app.shared.config import ModelSettings
from app.shared.errors import ServiceError, UnauthorizedError, error_dict
from .models import ErrorInfo, TeachingChatRequest, TeachingResponse, Usage
from .sse import encode
from .teaching_service import TeachingChatService
from .usage_stats import stats
router = APIRouter()

# 流式 keepalive 间隔：长时间无业务分片时发送 ": ping" 注释帧。测试可 patch 该常量。
KEEPALIVE_TIMEOUT_SECONDS = 15.0


def _usage_of(value) -> Usage | None:
    if value is None:
        return None
    if isinstance(value, Usage):
        return value
    return Usage.model_validate(value)

def service_dependency() -> TeachingChatService: raise RuntimeError("teaching service is not initialized")


def settings_dependency(request: Request) -> ModelSettings:
    settings = getattr(request.app.state, "settings", None)
    if settings is None:
        raise RuntimeError("model settings are not initialized")
    return settings

def error_payload(req, error: ServiceError):
    response = TeachingResponse(requestId=getattr(req, "request_id", "") or "", conversationId=getattr(req, "conversation_id", "") or "", turnId=getattr(req, "turn_id", 1), model=None, finishReason="error", error=ErrorInfo(**error_dict(error)))
    return JSONResponse(status_code=error.status_code, content=response.model_dump(by_alias=True))

def _unexpected_error() -> ServiceError:
    return ServiceError("INTERNAL_ERROR", "internal service error", 500, True)


def _api_key_of(authorization: str | None) -> str:
    # 只记 Key 本身（用于区分调用方），不含 Bearer 前缀
    return (authorization or "").removeprefix("Bearer ").strip() or "anonymous"


def _client_ip(request: Request) -> str:
    # 经过 Nginx 反代时取 X-Real-IP（我们的 nginx 配置已设置）；直连后端端口时退化为 socket 对端
    real_ip = (request.headers.get("x-real-ip") or "").strip()
    if real_ip:
        return real_ip
    forwarded = (request.headers.get("x-forwarded-for") or "").split(",")[0].strip()
    if forwarded:
        return forwarded
    return request.client.host if request.client else "unknown"


async def _record(request_id: str, chat_type: str, model: str | None, api_key: str, client_ip: str, status: str, usage=None, error_code: str | None = None):
    entry = {"request_id": request_id, "chat_type": chat_type, "model": model, "api_key": api_key, "client_ip": client_ip, "status": status}
    if usage is not None:
        entry["usage"] = {"input_tokens": usage.input_tokens, "output_tokens": usage.output_tokens, "total_tokens": usage.total_tokens}
    if error_code:
        entry["error_code"] = error_code
    await stats.record(**entry)


@router.get("/v1/stats/usage")
async def usage_stats(authorization: str | None = Header(None), settings: ModelSettings = Depends(settings_dependency), days: int = Query(30, ge=1, le=365)):
    if not authorized(authorization, settings.api_keys, settings.auth_disabled): return JSONResponse(status_code=401, content={"error": "unauthorized"})
    return stats.summary(days)


@router.post("/v1/chat/teaching")
async def teaching_chat(request: Request, authorization: str | None = Header(None), service: TeachingChatService = Depends(service_dependency), settings: ModelSettings = Depends(settings_dependency)):
    if not authorized(authorization, settings.api_keys, settings.auth_disabled): return error_payload(None, UnauthorizedError())
    api_key = _api_key_of(authorization)
    client_ip = _client_ip(request)
    try: chat = TeachingChatRequest.model_validate(await request.json())
    except (json.JSONDecodeError, ValidationError) as exc: return error_payload(None, ServiceError("INVALID_ARGUMENT", str(exc), 400))
    try: prepared = await service.prepare(chat)
    except ServiceError as exc:
        await _record(chat.request_id or "", chat.metadata.chat_type, None, api_key, client_ip, "error", error_code=exc.code)
        return error_payload(chat, exc)
    except Exception:
        await _record(chat.request_id or "", chat.metadata.chat_type, None, api_key, client_ip, "error", error_code="INTERNAL_ERROR")
        return error_payload(chat, _unexpected_error())
    if not chat.stream:
        try:
            response = (await service.generate(prepared)).model_dump(by_alias=True)
            usage_obj = _usage_of(response.get("usage"))
            await _record(chat.request_id or "", chat.metadata.chat_type, response.get("model"), api_key, client_ip, "ok", usage=usage_obj)
            return response
        except ServiceError as exc:
            await _record(chat.request_id or "", chat.metadata.chat_type, None, api_key, client_ip, "error", error_code=exc.code)
            return error_payload(chat, exc)
        except Exception:
            await _record(chat.request_id or "", chat.metadata.chat_type, None, api_key, client_ip, "error", error_code="INTERNAL_ERROR")
            return error_payload(chat, _unexpected_error())
    async def stream():
        stream_iter = service.stream(prepared).__aiter__()
        final_usage, final_model = None, chat.model
        status, error_code = "ok", None
        # 用 asyncio.wait 而非 wait_for 做 keepalive：wait_for 超时会取消挂起的 __anext__，
        # 使生成器被关闭——首帧前静默可能超过 15s 的业务（如 case_diagnosis_card 在模型思考期
        # 不产出任何分片）会被掐断，响应只剩 ping。
        pending: asyncio.Future | None = None
        try:
            while True:
                if pending is None:
                    pending = asyncio.ensure_future(stream_iter.__anext__())
                done, _ = await asyncio.wait({pending}, timeout=KEEPALIVE_TIMEOUT_SECONDS)
                if not done:
                    yield ": ping\n\n"
                    continue
                try:
                    item = pending.result()
                except StopAsyncIteration:
                    break
                pending = None
                final_model = item.model or final_model
                if item.usage is not None: final_usage = item.usage
                if item.finish_reason == "error":
                    status, error_code = "error", (item.error.code if item.error else "UNKNOWN")
                yield encode(item)
        except ServiceError as exc:
            status, error_code = "error", exc.code
            yield encode(TeachingResponse(requestId=chat.request_id or "", conversationId=chat.conversation_id or "", turnId=chat.turn_id, model=None, finishReason="error", error=ErrorInfo(**error_dict(exc))))
        except Exception:
            status, error_code = "error", "INTERNAL_ERROR"
            yield encode(TeachingResponse(requestId=chat.request_id or "", conversationId=chat.conversation_id or "", turnId=chat.turn_id, model=None, finishReason="error", error=ErrorInfo(**error_dict(_unexpected_error()))))
        finally:
            if pending is not None:
                pending.cancel()
            await _record(chat.request_id or "", chat.metadata.chat_type, final_model, api_key, client_ip, status, usage=final_usage, error_code=error_code)
    return StreamingResponse(stream(), media_type="text/event-stream", headers={"Cache-Control":"no-cache", "Connection":"keep-alive"})
