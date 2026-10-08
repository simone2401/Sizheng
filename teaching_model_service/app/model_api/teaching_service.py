from __future__ import annotations
import re
import uuid
from dataclasses import dataclass
from typing import Any, AsyncIterator
from .models import TeachingChatRequest, TeachingResponse, Usage
from .prompts import SOCRATIC_CASE_PROMPT, LESSON_PLAN_CONTRACT, DIAGNOSIS_CARD_PROMPT
from .diagnosis import detect_sufficient, parse_card
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
            ideology_ids = [item.strip() for item in (meta.ideology_ids or []) if item and item.strip()]
            if ideology_ids:
                resource_params["ideologyIDs"] = ideology_ids
        resource_result = await self.resource_client.query(**resource_params)
        resource = resource_result.model_dump(by_alias=True) if hasattr(resource_result, "model_dump") else resource_result
        labels = sorted(dict.fromkeys(x.get("l1_label", "") for x in resource.get("ideologyTags", {}).get("level1", []) if x.get("l1_label")))
        if meta.chat_type == "case_diagnosis_card":
            # 诊断卡为快照式调用：messages[0] 为案例全文，其后为全量历史问答（末条不要求 USER）
            context = _case_resource_context(resource)
            case_text = "\n".join(x.text for x in request.messages[0].content)
            transcript = _conversation_text(request.messages[1:])
            system_prompt, mode = DIAGNOSIS_CARD_PROMPT, "diagnosis_card"
            user_prompt = "\n".join((
                "【教材与案例资源】", context,
                "【案例全文】", case_text,
                "【对话记录】", transcript or "（暂无对话）",
                "请严格按系统指令的输出格式完成两项任务。",
            ))
            self.input_guard.check(system_prompt)
            self.input_guard.check(user_prompt)
            return PreparedTeachingRequest(request, system_prompt, user_prompt, mode, labels)
        conversation = _conversation_text(request.messages[:-1])
        current_request = _current_user_text(request)
        if meta.chat_type == "case_guide_study":
            context = _case_resource_context(resource)
            system_prompt, mode = SOCRATIC_CASE_PROMPT, "case_guide"
            user_prompt = "\n".join(("【教材与案例资源】", context, "【对话记录】", conversation, "【教师当前请求】", current_request))
        else:
            context = _json_context(resource)
            supplemental_materials = _extract_supplemental_materials(request, meta.original_lesson_plan)
            mode_text = "统一按 expert-0731-v1 模版输出；如提供补充材料，仅参考其内容，不沿用其格式"
            format_rule = "最终输出不得复用补充材料中的标题层级、段落编排或表格样式，必须完整落到 expert-0731-v1 结构"
            system_prompt, mode = LESSON_PLAN_CONTRACT, "lesson_plan_assist"
            user_prompt = "\n".join((f"【工作模式】{mode_text}", f"【格式硬约束】{format_rule}", f"【补充材料】{supplemental_materials or '无'}", "【教材与匹配资源】", context, "【思政标签】" + "、".join(labels), "【对话记录】", conversation, "【教师当前请求】", current_request))
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
        if prepared.mode == "diagnosis_card":
            # 诊断卡：content 恒为空，结构化内容由 diagnosisCard 承载；解析失败抛 MODEL_FORMAT_VIOLATION
            card = parse_card(result.content)
            response = response_for(prepared.request, result.model, prepared.l1_labels, reasoning, "", result.usage, _normalize_finish_reason(result.finish_reason))
            response.diagnosis_card = card
            return response
        return response_for(prepared.request, result.model, prepared.l1_labels, reasoning, result.content, result.usage, _normalize_finish_reason(result.finish_reason))

    async def stream(self, prepared: PreparedTeachingRequest) -> AsyncIterator[TeachingResponse]:
        if prepared.mode == "diagnosis_card":
            # 两段式：首业务分片仅含 sufficient（供调用方提前分支），终止分片为唯一权威整卡；
            # 中间不转发 content/reasoning 增量（协议约定 content 恒为空）
            accumulated = ""
            emitted_first = False
            last_model = prepared.request.model
            usage = None
            finish: str | None = None
            async for item in self.model_client.stream(prepared.system_prompt, prepared.user_prompt, prepared.mode, prepared.request.model):
                last_model = item.get("model") or last_model
                piece = item.get("content", "")
                if piece:
                    accumulated += piece
                    if not emitted_first:
                        sufficient = detect_sufficient(accumulated)
                        if sufficient is not None:
                            emitted_first = True
                            yield response_for(prepared.request, last_model, prepared.l1_labels, "", "", None, None, diagnosis_card={"sufficient": sufficient, "sections": None})
                reason = _normalize_finish_reason(item.get("finish_reason"))
                if reason:
                    finish = reason
                if item.get("usage"):
                    usage = item["usage"]
            self.output_guard.check(accumulated)
            card = parse_card(accumulated)  # 失败抛 ModelClientError，由 router 转为 error 终止分片
            yield response_for(prepared.request, last_model, prepared.l1_labels, "", "", usage, finish or "stop", diagnosis_card=card)
            return
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


def response_for(request: TeachingChatRequest, model: str | None, labels: list[str], reasoning: str | None, content: str, usage: Usage | None, finish: str | None, diagnosis_card: dict | None = None) -> TeachingResponse:
    return TeachingResponse(requestId=request.request_id or "", conversationId=request.conversation_id or "", turnId=request.turn_id, model=model, l1_labels=labels, reasoning_content=reasoning, content=content, finishReason=finish, usage=usage, diagnosisCard=diagnosis_card)

def _conversation_text(messages):
    return "\n".join(
        f"{i}. {'用户' if m.role == 'USER' else '助手'}：{'；'.join(x.text for x in m.content)}"
        for i, m in enumerate(messages, 1)
    )
def _current_user_text(request): return "\n".join(item.text for item in request.messages[-1].content)


def _extract_supplemental_materials(request, metadata_material: str | None = None):
    materials = []
    if metadata_material and metadata_material.strip():
        materials.append(metadata_material.strip())
    for message in request.messages:
        if message.role == "USER":
            text = "\n".join(x.text for x in message.content)
            materials.extend(_extract_marked_materials(text))
    if not materials:
        return None
    merged = "\n\n".join(dict.fromkeys(item for item in materials if item.strip()))
    return merged[:30000] if merged else None


def _extract_marked_materials(text: str) -> list[str]:
    marker = "【补充材料】"
    results: list[str] = []

    for match in re.finditer(r"【补充材料】(.*?)【补充材料结束】", text, flags=re.S):
        value = match.group(1).strip()
        if value:
            results.append(value)

    if results:
        return results

    positions = []
    start = 0
    while True:
        index = text.find(marker, start)
        if index < 0:
            break
        positions.append(index)
        start = index + len(marker)

    if len(positions) < 2:
        return results

    for index in range(0, len(positions) - 1, 2):
        begin = positions[index] + len(marker)
        end = positions[index + 1]
        value = text[begin:end].strip()
        if value:
            results.append(value)
    return results


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
