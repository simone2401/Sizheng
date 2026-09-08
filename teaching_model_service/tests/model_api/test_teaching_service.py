import asyncio

import pytest
from conftest import BASE, FakeModelClient, lesson_payload

from app.model_api.models import TeachingChatRequest, Usage
from app.model_api.teaching_service import TeachingChatService
from app.shared.config import ModelSettings


def test_case_prompt_contains_socratic_rules(model_client):
    _, resource, fake_model = model_client
    request = TeachingChatRequest.model_validate(BASE)
    service = TeachingChatService(resource_client=resource, model_client=fake_model)
    prepared = asyncio.run(service.prepare(request))
    assert prepared.mode == "case_guide"
    assert "每轮只提出一个核心问题" in prepared.system_prompt
    assert "贴标签" in prepared.system_prompt and "喧宾夺主" in prepared.system_prompt


def test_original_plan_uses_original_format_mode(model_client):
    _, resource, fake_model = model_client
    payload = lesson_payload("请修改原教案中的教学过程")
    payload["metadata"]["originalLessonPlan"] = "# 我原来的标题\n## 教学过程\n原有内容"
    service = TeachingChatService(resource_client=resource, model_client=fake_model)
    prepared = asyncio.run(service.prepare(TeachingChatRequest.model_validate(payload)))
    assert prepared.mode == "lesson_plan_assist"
    assert "我原来的标题" in prepared.user_prompt
    assert "优先保留原章节和格式" in prepared.user_prompt


def test_prompt_history_does_not_repeat_latest_user_message(model_client):
    _, resource, fake_model = model_client
    payload = lesson_payload("请围绕实验现象补充互动提问")
    payload["messages"] = [
        {"role": "USER", "content": [{"type": "TEXT", "text": "先回顾上节内容"}]},
        {"role": "ASSISTANT", "content": [{"type": "TEXT", "text": "可以从密度定义入手"}]},
        {"role": "USER", "content": [{"type": "TEXT", "text": "请围绕实验现象补充互动提问"}]},
    ]
    service = TeachingChatService(resource_client=resource, model_client=fake_model)
    prepared = asyncio.run(service.prepare(TeachingChatRequest.model_validate(payload)))
    dialogue_part = prepared.user_prompt.split("【教师当前请求】", 1)[0]
    assert "先回顾上节内容" in dialogue_part
    assert "可以从密度定义入手" in dialogue_part
    assert "请围绕实验现象补充互动提问" not in dialogue_part


def test_stream_without_terminal_chunk_gets_stop_event(model_client):
    _, resource, _ = model_client

    class UnterminatedModel(FakeModelClient):
        async def stream(self, *args, **kwargs):
            yield {
                "content": "片段",
                "reasoning_content": "",
                "model": "fake-model",
                "finish_reason": None,
                "usage": None,
            }

    service = TeachingChatService(resource, model_client=UnterminatedModel())
    prepared = asyncio.run(service.prepare(TeachingChatRequest.model_validate(lesson_payload("请生成教案", True))))

    async def collect():
        return [item async for item in service.stream(prepared)]

    payloads = asyncio.run(collect())
    assert payloads[-1].finish_reason == "stop"
    assert sum(item.finish_reason == "stop" for item in payloads) == 1


def test_stream_defaults_to_true():
    request = TeachingChatRequest.model_validate({key: value for key, value in BASE.items() if key != "stream"})
    assert request.stream is True


def test_usage_aliases_are_camel_case():
    value = Usage(inputTokens=1, outputTokens=2, totalTokens=3).model_dump(by_alias=True)
    assert value == {"inputTokens": 1, "outputTokens": 2, "totalTokens": 3}


def test_invalid_model_backend_is_rejected(monkeypatch):
    monkeypatch.setenv("MODEL_BACKEND", "unknown")
    with pytest.raises(ValueError, match="MODEL_BACKEND"):
        ModelSettings.from_env()
