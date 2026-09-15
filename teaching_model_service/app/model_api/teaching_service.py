from __future__ import annotations
import re
import uuid
from dataclasses import dataclass
from typing import Any, AsyncIterator
from .models import TeachingChatRequest, TeachingResponse, Usage
from .prompts import SOCRATIC_CASE_PROMPT, LESSON_PLAN_CONTRACT
from .resource_client import ResourceClient
from .model_clients import MockModelClient, ZhipuModelClient
from .safety import InputGuard, OutputGuard
from app.shared.config import ModelSettings
from app.shared.errors import ModelClientError


def _normalize_finish_reason(value: str | None) -> str | None:
    if value is None or value == "":
        return None
    if value in {"stop", "length", "tool_calls", "content_filter"}:
        return value
    if value == "error":
        raise ModelClientError("MODEL_RESPONSE_INVALID", "model returned an error finish reason", 502, False)
    raise ModelClientError("MODEL_RESPONSE_INVALID", f"unsupported model finish reason: {value}", 502, False)

@dataclass
class PreparedTeachingRequest:
    request: TeachingChatRequest
    system_prompt: str
    user_prompt: str
    mode: str
    l1_labels: list[str]

class TeachingChatService:
    def __init__(self, resource_client: ResourceClient, model_client: Any | None = None, settings: ModelSettings | None = None):
        self.resource_client, self.settings = resource_client, settings or ModelSettings.from_env()
        if model_client is not None:
            self.model_client = model_client
        elif self.settings.model_backend == "zhipu":
            self.model_client = ZhipuModelClient(
                self.settings.zhipu_api_key,
                self.settings.zhipu_model,
                self.settings.model_timeout,
                base_url=self.settings.zhipu_base_url,
                client=getattr(resource_client, "client", None),
            )
        else:
            self.model_client = MockModelClient()
        self.input_guard, self.output_guard = InputGuard(), OutputGuard()

    async def prepare(self, request: TeachingChatRequest) -> PreparedTeachingRequest:
        if request.request_id is None: object.__setattr__(request, "request_id", f"REQ{uuid.uuid4().hex[:14]}")
        if request.conversation_id is None: object.__setattr__(request, "conversation_id", f"CNV{uuid.uuid4().hex[:14]}")
        meta = request.metadata
        resource_params = {
            "schoolLevel": meta.school_level,
            "subject": meta.subject,
            "textbookVersion": meta.textbook_version,
            "chapter": meta.chapter,
            "lesson": meta.lesson,
        }
        if meta.chat_type == "lesson_plan_assist":
            resource_params["knowledgePoints"] = meta.knowledge_points
            ideology_ids = [item.strip() for item in (meta.ideology_ids or "").split(",") if item.strip()]
            if ideology_ids:
                resource_params["ideologyIDs"] = ideology_ids
        resource_result = await self.resource_client.query(**resource_params)
        resource = resource_result.model_dump(by_alias=True) if hasattr(resource_result, "model_dump") else resource_result
        labels = sorted(dict.fromkeys(x.get("l1_label", "") for x in resource.get("ideologyTags", {}).get("level1", []) if x.get("l1_label")))
        conversation = _conversation_text(request.messages[:-1])
        current_request = _current_user_text(request)
        if meta.chat_type == "case_guide_study":
            context = _case_resource_context(resource)
            system_prompt, mode = SOCRATIC_CASE_PROMPT, "case_guide"
            user_prompt = "\n".join(("【教材与案例资源】", context, "【对话记录】", conversation, "【教师当前请求】", current_request))
        else:
            context = _json_context(resource)
            original = meta.original_lesson_plan or _extract_original_plan(request)
            mode_text = "带原教案修改/融合：优先保留原章节和格式，只按需求修改" if original else "从零生成：完整执行 expert-0731-v1 合同"
            system_prompt, mode = LESSON_PLAN_CONTRACT, "lesson_plan_assist"
            user_prompt = "\n".join((f"【工作模式】{mode_text}", f"【原教案】{original or '无'}", "【教材与匹配资源】", context, "【思政标签】" + "、".join(labels), "【对话记录】", conversation, "【教师当前请求】", current_request))
        self.input_guard.check(system_prompt)
        self.input_guard.check(user_prompt)
        return PreparedTeachingRequest(request, system_prompt, user_prompt, mode, labels)

    async def generate(self, prepared: PreparedTeachingRequest) -> TeachingResponse:
        result = await self.model_client.generate(prepared.system_prompt, prepared.user_prompt, prepared.mode, prepared.request.model)
        if prepared.mode == "lesson_plan_assist":
            result.content = _normalize_lesson_markdown(result.content)
        self.output_guard.check(result.content)
        if result.reasoning_content:
            self.output_guard.check(result.reasoning_content)
        reasoning = result.reasoning_content
        return response_for(prepared.request, result.model, prepared.l1_labels, reasoning, result.content, result.usage, _normalize_finish_reason(result.finish_reason))

    async def stream(self, prepared: PreparedTeachingRequest) -> AsyncIterator[TeachingResponse]:
        emitted_terminal = False
        last_model = prepared.request.model
        raw_content_buffer = ""
        emitted_content = ""
        async for item in self.model_client.stream(prepared.system_prompt, prepared.user_prompt, prepared.mode, prepared.request.model):
            last_model = item.get("model") or last_model
            reasoning = item.get("reasoning_content")
            chunk = item.get("content", "")
            content = ""
            if prepared.mode == "lesson_plan_assist" and chunk:
                raw_content_buffer += chunk
                normalized = _normalize_lesson_markdown(raw_content_buffer)
                prefix_length = 0
                max_prefix = min(len(emitted_content), len(normalized))
                while prefix_length < max_prefix and emitted_content[prefix_length] == normalized[prefix_length]:
                    prefix_length += 1
                content = normalized[prefix_length:]
                emitted_content = normalized
            elif chunk:
                content = chunk
            if reasoning:
                self.output_guard.check(reasoning)
            if content:
                self.output_guard.check(content)
            if reasoning or content:
                yield response_for(prepared.request, last_model, prepared.l1_labels, reasoning, content, None, None)
            finish_reason = _normalize_finish_reason(item.get("finish_reason"))
            if item.get("usage") or finish_reason:
                if emitted_terminal:
                    continue
                emitted_terminal = True
                yield response_for(prepared.request, last_model, prepared.l1_labels, "", "", item.get("usage"), finish_reason or "stop")
        if not emitted_terminal:
            yield response_for(prepared.request, last_model, prepared.l1_labels, "", "", None, "stop")


def response_for(request: TeachingChatRequest, model: str | None, labels: list[str], reasoning: str | None, content: str, usage: Usage | None, finish: str | None) -> TeachingResponse:
    return TeachingResponse(requestId=request.request_id or "", conversationId=request.conversation_id or "", turnId=request.turn_id, model=model, l1_labels=labels, reasoning_content=reasoning, content=content, finishReason=finish, usage=usage)

def _conversation_text(messages):
    return "\n".join(
        f"{i}. {'用户' if m.role == 'USER' else '助手'}：{'；'.join(x.text for x in m.content)}"
        for i, m in enumerate(messages, 1)
    )
def _current_user_text(request): return "\n".join(item.text for item in request.messages[-1].content)
def _extract_original_plan(request):
    for message in reversed(request.messages):
        if message.role == "USER":
            text = "\n".join(x.text for x in message.content)
            for marker in ("原教案：", "原始教案：", "待修改教案："):
                if marker in text and text.split(marker, 1)[1].strip(): return text.split(marker, 1)[1].strip()[:30000]
    return None
def _case_resource_context(resource):
    return "\n".join((
        f"教材：{resource['textbook'].get('textbook_name', '')}",
        f"章节：{resource['chapter'].get('chapter_title', '')}",
        f"小节：{resource['section'].get('section_title', '')}",
        "教材原文：" + "\n".join(x.get('text', '')[:500] for x in resource.get('textbookChunks', [])[:8]),
        "课程标准：" + "；".join(x.get('item_content', '') for x in resource.get('curriculumStandards', [])[:6]),
    ))


def _json_context(resource):
    return "\n".join((f"教材：{resource['textbook'].get('textbook_name', '')}", f"章节：{resource['chapter'].get('chapter_title', '')}", f"小节：{resource['section'].get('section_title', '')}", "知识点：" + "；".join(x['title'] for x in resource['knowledgePoints']), "教材原文：" + "\n".join(x.get('text', '')[:500] for x in resource['textbookChunks'][:8]), "课程标准：" + "；".join(x.get('item_content', '') for x in resource['curriculumStandards'][:6]), "思政资源：" + "\n".join(x.get('textbook_original_excerpt', '') for x in resource['ideologyParagraphs'][:6]), "思政标签：" + "、".join(x.get('l3_label', '') for x in resource.get('ideologyTags', {}).get('level3', [])[:12])))


def _normalize_lesson_markdown(text: str) -> str:
    value = text
    value = value.replace("\r\n", "\n")
    value = re.sub(r"(?m)^\s*\\+(?=#{1,6}\s)", "", value)
    value = re.sub(r"(?m)^\s*\\+(?=-\s)", "", value)
    value = re.sub(r"(?m)^\s*\\+(?=\|)", "", value)
    value = re.sub(r"\\([#|\-])", r"\1", value)
    value = re.sub(r"(?m)^\s*\\\s*$", "", value)
    value = re.sub(r"(?m)^\s*\(\s*$", "", value)
    value = re.sub(r"(?m)^\s*\)\s*$", "", value)
    return value.rstrip()
