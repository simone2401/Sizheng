import asyncio
import json

import httpx
import pytest

from app.model_api.model_clients import ZhipuModelClient
from app.shared.errors import ModelClientError


SYSTEM_PROMPT = "你是课程思政备课助手。"
USER_PROMPT = "【教材资源】密度的应用\n【教师当前请求】请生成教案"


def test_non_stream_request_contains_system_and_user_messages():
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen.update(json.loads(request.content))
        return httpx.Response(
            200,
            json={
                "model": "glm-requested",
                "choices": [{"message": {"content": "# 教案", "reasoning_content": None}, "finish_reason": "stop"}],
                "usage": {"prompt_tokens": 1, "completion_tokens": 2, "total_tokens": 3},
            },
        )

    async def run():
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            return await ZhipuModelClient("test-key", client=client).generate(SYSTEM_PROMPT, USER_PROMPT, "lesson_plan_assist", "glm-requested")

    result = asyncio.run(run())

    assert seen["model"] == "glm-requested"
    assert seen["stream"] is False
    assert seen["messages"] == [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": USER_PROMPT},
    ]
    assert result.reasoning_content is None


def test_request_model_defaults_to_configured_model():
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen.update(json.loads(request.content))
        return httpx.Response(
            200,
            json={
                "model": "glm-5.2",
                "choices": [{"message": {"content": "# 教案", "reasoning_content": None}, "finish_reason": "stop"}],
                "usage": {"prompt_tokens": 1, "completion_tokens": 2, "total_tokens": 3},
            },
        )

    async def run():
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            return await ZhipuModelClient("test-key", model="glm-5.2", client=client).generate(SYSTEM_PROMPT, USER_PROMPT, "lesson_plan_assist")

    asyncio.run(run())

    assert seen["model"] == "glm-5.2"
    assert seen["messages"][1] == {"role": "user", "content": USER_PROMPT}


def test_stream_request_contains_system_and_user_messages():
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen.update(json.loads(request.content))
        return httpx.Response(200, content="data: [DONE]\n\n")

    async def run():
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            return [item async for item in ZhipuModelClient("test-key", client=client).stream(SYSTEM_PROMPT, USER_PROMPT, "lesson_plan_assist", "glm-5.3-flash")]

    assert asyncio.run(run()) == []
    assert seen["model"] == "glm-5.3-flash"
    assert seen["stream"] is True
    assert seen["messages"] == [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": USER_PROMPT},
    ]


@pytest.mark.parametrize(
    ("upstream_status", "expected_status", "expected_retriable"),
    [(400, 502, False), (429, 429, True), (500, 502, True)],
)
def test_upstream_errors_have_http_status_not_boolean(upstream_status, expected_status, expected_retriable):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(upstream_status)

    async def run():
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            await ZhipuModelClient("test-key", client=client).generate(SYSTEM_PROMPT, USER_PROMPT, "lesson_plan_assist")

    with pytest.raises(ModelClientError) as caught:
        asyncio.run(run())
    assert caught.value.status_code == expected_status
    assert caught.value.retriable is expected_retriable
