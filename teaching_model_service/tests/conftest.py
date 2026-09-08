import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.model_api.main import app as model_app
from app.model_api.model_clients import ModelResult
from app.model_api.router import service_dependency as model_service_dependency
from app.model_api.router import settings_dependency as model_settings_dependency
from app.model_api.teaching_service import TeachingChatService
from app.model_api.models import Usage
from app.resource_api.main import app as resource_app
from app.resource_api.repository import ResourceRepository
from app.resource_api.router import service_dependency as resource_service_dependency
from app.resource_api.router import settings_dependency as resource_settings_dependency
from app.resource_api.service import ResourceService
from app.shared.config import ModelSettings, ResourceSettings


RESOURCE = {
    "textbook": {"textbook_name": "人教版物理八年级上册"},
    "chapter": {"chapter_title": "第六章 质量与密度"},
    "section": {"section_title": "第4节 密度的应用"},
    "knowledgePoints": [{"title": "密度与材料选择"}],
    "textbookChunks": [{"text": "教材原文：密度是物质的一种特性。"}],
    "curriculumStandards": [{"item_content": "认识质量和密度，能解释相关现象。"}],
    "ideologyParagraphs": [{"textbook_original_excerpt": "思政段落：材料选择服务绿色生活。"}],
    "ideologyTags": {
        "level1": [{"l1_label": "家国责任"}],
        "level2": [{"l2_label": "责任意识"}],
        "level3": [{"l3_label": "生态文明"}],
    },
}

BASE = {
    "model": "glm-5.3-flash",
    "turnId": 1,
    "messages": [{"role": "USER", "content": [{"type": "TEXT", "text": "请开始案例导引学习"}]}],
    "metadata": {
        "chatType": "case_guide_study",
        "schoolLevel": "8年级上",
        "subject": "物理",
        "textbookVersion": "人教版",
        "chapter": "第六章",
        "lesson": "第4节",
    },
}


def lesson_payload(text: str, stream: bool = False):
    payload = json.loads(json.dumps(BASE))
    payload["stream"] = stream
    payload["messages"][0]["content"][0]["text"] = text
    payload["metadata"]["chatType"] = "lesson_plan_assist"
    payload["metadata"]["knowledgePoints"] = ["密度与材料选择"]
    return payload


class FakeResourceClient:
    def __init__(self):
        self.calls = []

    async def query(self, **params):
        self.calls.append(params)
        return RESOURCE


class FakeModelClient:
    def __init__(self):
        self.calls = []

    async def generate(self, system_prompt, user_prompt, response_mode, model=None):
        self.calls.append((system_prompt, user_prompt, response_mode, model))
        if response_mode == "case_guide":
            return ModelResult(
                "请先指出案例中的物理问题。",
                "不应透传",
                model or "fake-model",
                Usage(inputTokens=10, outputTokens=5, totalTokens=15),
            )
        return ModelResult(
            "# 教案\n\n## 教学设计",
            "已完成教材分析。",
            model or "fake-model",
            Usage(inputTokens=10, outputTokens=20, totalTokens=30),
        )

    async def stream(self, system_prompt, user_prompt, response_mode, model=None):
        self.calls.append((system_prompt, user_prompt, response_mode, model))
        yield {
            "content": "",
            "reasoning_content": "教材分析已完成。",
            "model": model or "fake-model",
            "finish_reason": None,
            "usage": None,
        }
        yield {
            "content": "# 教案",
            "reasoning_content": "",
            "model": model or "fake-model",
            "finish_reason": None,
            "usage": None,
        }
        yield {
            "content": "",
            "reasoning_content": "",
            "model": model or "fake-model",
            "finish_reason": "stop",
            "usage": Usage(inputTokens=10, outputTokens=20, totalTokens=30),
        }


@pytest.fixture
def resource_client():
    settings = ResourceSettings(
        "127.0.0.1",
        8001,
        str(Path(__file__).parents[2] / "json_output" / "PEP8U_PHYSICS"),
        frozenset(),
        True,
        (),
    )
    repository = ResourceRepository(settings.resource_dir)
    repository.load()
    resource_app.dependency_overrides[resource_service_dependency] = lambda: ResourceService(repository)
    resource_app.dependency_overrides[resource_settings_dependency] = lambda: settings
    with TestClient(resource_app) as client:
        yield client
    resource_app.dependency_overrides.clear()


@pytest.fixture
def model_client():
    fake_resource = FakeResourceClient()
    fake_model = FakeModelClient()
    service = TeachingChatService(fake_resource, model_client=fake_model)
    settings = ModelSettings(
        "127.0.0.1",
        8000,
        "http://127.0.0.1:8001",
        "",
        frozenset(),
        True,
        "mock",
        "",
        "",
        "glm-5.3-flash",
        60.0,
        (),
    )
    model_app.dependency_overrides[model_service_dependency] = lambda: service
    model_app.dependency_overrides[model_settings_dependency] = lambda: settings
    with TestClient(model_app) as client:
        yield client, fake_resource, fake_model
    model_app.dependency_overrides.clear()
