import json

from conftest import BASE, FakeModelClient, lesson_payload

from app.model_api.main import app as model_app
from app.model_api.model_clients import ModelResult
from app.model_api.models import Usage
from app.model_api.router import settings_dependency as model_settings_dependency
from app.model_api.teaching_service import _normalize_lesson_markdown
from app.shared.config import ModelSettings


def test_lesson_generation_returns_reasoning_and_markdown(model_client):
    client, resource, fake_model = model_client
    data = client.post("/v1/chat/teaching", json=lesson_payload("请帮我生成课程思政教学设计教案")).json()
    assert data["content"].startswith("#")
    assert data["reasoning_content"] == "已完成教材分析。"
    assert data["l1_labels"] == ["家国责任"]
    assert "outputType" not in data and "outputs" not in data and "stage" not in data
    assert data["usage"] == {"inputTokens": 10, "outputTokens": 20, "totalTokens": 30}
    assert resource.calls[0]["knowledgePoints"] == ["密度与材料选择"]
    assert "思政段落" in fake_model.calls[0][1]


def test_case_has_content_only_and_filters_resources(model_client):
    client, resource, fake_model = model_client
    payload = dict(BASE)
    payload["stream"] = False
    payload["metadata"] = dict(BASE["metadata"], knowledgePoints=["密度与材料选择"])
    data = client.post("/v1/chat/teaching", json=payload).json()
    assert data["content"]
    assert data["reasoning_content"] == "不应透传"
    assert data["l1_labels"] == ["家国责任"]
    assert "knowledgePoints" not in resource.calls[0]
    user_prompt = fake_model.calls[0][1]
    assert all(
        value in user_prompt
        for value in ("人教版物理八年级上册", "第六章 质量与密度", "第4节 密度的应用", "教材原文", "课程标准")
    )
    assert all(value not in user_prompt for value in ("密度与材料选择", "思政段落", "生态文明"))


def test_sse_separates_fields_and_stop_event(model_client):
    client, _, _ = model_client
    response = client.post("/v1/chat/teaching", json=lesson_payload("请帮我生成教学设计教案", True))
    assert response.headers["content-type"].startswith("text/event-stream")
    payloads = [json.loads(line[6:]) for line in response.text.splitlines() if line.startswith("data: ")]
    assert any(item["content"] for item in payloads)
    assert any(item["reasoning_content"] for item in payloads)
    assert all(item["l1_labels"] == payloads[0]["l1_labels"] for item in payloads)
    assert payloads[-1]["finishReason"] == "stop"
    assert payloads[-1]["usage"]["totalTokens"] > 0


def test_sse_lesson_markdown_keeps_spaces_and_blank_lines_across_tiny_chunks(model_client):
    client, resource, _ = model_client

    class TinyChunkModel(FakeModelClient):
        async def stream(self, *args, **kwargs):
            for piece in ("##", " 标", "题", "\n\n", "第一", "段。"):
                yield {
                    "content": piece,
                    "reasoning_content": "",
                    "model": "fake-model",
                    "finish_reason": None,
                    "usage": None,
                }
            yield {
                "content": "",
                "reasoning_content": "",
                "model": "fake-model",
                "finish_reason": "stop",
                "usage": Usage(inputTokens=1, outputTokens=1, totalTokens=2),
            }

    from app.model_api.router import service_dependency as model_service_dependency
    from app.model_api.teaching_service import TeachingChatService

    service = TeachingChatService(resource, model_client=TinyChunkModel())
    model_app.dependency_overrides[model_service_dependency] = lambda: service

    response = client.post("/v1/chat/teaching", json=lesson_payload("请生成教案", True))
    payloads = [json.loads(line[6:]) for line in response.text.splitlines() if line.startswith("data: ")]

    rendered = "".join(item["content"] for item in payloads if item.get("content"))
    assert rendered == "## 标题\n\n第一段。"


def test_normalize_lesson_markdown_keeps_leading_whitespace():
    raw = "\n\n    代码块前导缩进\n"
    assert _normalize_lesson_markdown(raw) == "\n\n    代码块前导缩进"


def test_normalize_lesson_markdown_keeps_literal_escape_for_asterisk():
    raw = "\\*保留星号"
    assert _normalize_lesson_markdown(raw) == "\\*保留星号"


def test_model_auth_rejects_missing_key(model_client):
    client, _, _ = model_client
    settings = ModelSettings(
        "127.0.0.1",
        8000,
        "http://127.0.0.1:8001",
        "",
        frozenset({"model-key"}),
        False,
        "mock",
        "",
        "",
        "glm-5.3-flash",
        60.0,
        (),
    )
    model_app.dependency_overrides[model_settings_dependency] = lambda: settings
    response = client.post("/v1/chat/teaching", json=lesson_payload("请生成教案"))
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHORIZED"


def test_model_auth_accepts_valid_key(model_client):
    client, _, _ = model_client
    settings = ModelSettings(
        "127.0.0.1",
        8000,
        "http://127.0.0.1:8001",
        "",
        frozenset({"model-key"}),
        False,
        "mock",
        "",
        "",
        "glm-5.3-flash",
        60.0,
        (),
    )
    model_app.dependency_overrides[model_settings_dependency] = lambda: settings
    response = client.post(
        "/v1/chat/teaching",
        headers={"Authorization": "Bearer model-key"},
        json=lesson_payload("请生成教案"),
    )
    assert response.status_code == 200


def test_length_finish_reason_is_returned(model_client):
    client, resource, _ = model_client

    class TruncatedModel(FakeModelClient):
        async def generate(self, *args, **kwargs):
            return ModelResult(
                "# 教案",
                "",
                "fake-model",
                Usage(inputTokens=1, outputTokens=1, totalTokens=2),
                "length",
            )

    from app.model_api.router import service_dependency as model_service_dependency
    from app.model_api.teaching_service import TeachingChatService

    service = TeachingChatService(resource, model_client=TruncatedModel())
    model_app.dependency_overrides[model_service_dependency] = lambda: service
    response = client.post("/v1/chat/teaching", json=lesson_payload("请生成教案"))
    assert response.status_code == 200
    assert response.json()["finishReason"] == "length"


def test_sse_keepalive_ping_is_emitted(monkeypatch, model_client):
    import asyncio

    client, resource, _ = model_client

    class SlowModel(FakeModelClient):
        async def stream(self, *args, **kwargs):
            import asyncio

            await asyncio.sleep(0.02)
            yield {
                "content": "",
                "reasoning_content": "",
                "model": "fake-model",
                "finish_reason": "stop",
                "usage": Usage(inputTokens=1, outputTokens=1, totalTokens=2),
            }

    from app.model_api.router import service_dependency as model_service_dependency
    from app.model_api.teaching_service import TeachingChatService

    original_wait_for = asyncio.wait_for

    async def fast_wait_for(coro, timeout):
        return await original_wait_for(coro, 0.001)

    monkeypatch.setattr("app.model_api.router.asyncio.wait_for", fast_wait_for)
    service = TeachingChatService(resource, model_client=SlowModel())
    model_app.dependency_overrides[model_service_dependency] = lambda: service
    response = client.post("/v1/chat/teaching", json=lesson_payload("请生成教案", True))
    assert ": ping" in response.text
