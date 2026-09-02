import json

from fastapi.testclient import TestClient

from app.main import app, teaching_service
from app.models import TeachingChatRequest
from app.service import ModelResult, Usage

client = TestClient(app)
BASE = {
    "model": "zhipu",
    "turnId": 1,
    "messages": [{"role": "USER", "content": [{"type": "TEXT", "text": "请开始案例导学"}]}],
    "metadata": {"chatType": "case_guide_study", "schoolLevel": "8年级上", "subject": "物理", "textbookVersion": "人教版", "chapter": "第六章 质量与密度", "lesson": "第4节 密度的应用"},
}


def lesson_payload(text: str, stream: bool = False):
    payload = json.loads(json.dumps(BASE))
    payload["stream"] = stream
    payload["messages"][0]["content"][0]["text"] = text
    payload["metadata"]["chatType"] = "lesson_plan_assist"
    payload["metadata"]["knowledgePoints"] = ["密度与材料选择"]
    return payload


def test_resources_returns_structured_context():
    response = client.get("/v1/teaching/resources", params={"schoolLevel": "8年级上", "subject": "物理", "textbookVersion": "人教版", "chapter": "第六章", "lesson": "第4节"})
    assert response.status_code == 200
    data = response.json()
    assert data["section"]["section_title"] == "第4节 密度的应用"
    assert "textbookChunks" in data and "ideologyTags" in data


def test_lesson_generation_returns_reasoning_and_markdown():
    data = client.post("/v1/chat/teaching", json=lesson_payload("请帮我生成课程思政教学设计教案")).json()
    assert data["content"].startswith("#")
    assert "教材分析" in data["reasoning_content"]
    assert data["l1_labels"]
    assert "outputType" not in data and "outputs" not in data and "stage" not in data
    assert data["usage"] == {"inputTokens": data["usage"]["inputTokens"], "outputTokens": data["usage"]["outputTokens"], "totalTokens": data["usage"]["totalTokens"]}


def test_case_has_content_only():
    payload = dict(BASE)
    payload["stream"] = False
    data = client.post("/v1/chat/teaching", json=payload).json()
    assert data["content"]
    assert data["reasoning_content"] == ""
    assert data["l1_labels"]


def test_sse_separates_fields_and_stop_event():
    response = client.post("/v1/chat/teaching", json=lesson_payload("请帮我生成教学设计教案", True))
    payloads = [json.loads(line[6:]) for line in response.text.splitlines() if line.startswith("data: ")]
    assert any(item["content"] for item in payloads)
    assert any(item["reasoning_content"] for item in payloads)
    assert all(item["l1_labels"] == payloads[0]["l1_labels"] for item in payloads)
    assert payloads[-1]["finishReason"] == "stop"
    assert payloads[-1]["usage"]["totalTokens"] > 0


def test_invalid_resource_returns_not_found():
    response = client.get("/v1/teaching/resources", params={"schoolLevel": "8年级上", "subject": "物理", "textbookVersion": "不存在", "chapter": "第六章", "lesson": "第4节"})
    assert response.status_code == 404


def test_case_prompt_contains_socratic_rules():
    prompt, mode, generate_plan, l1_labels = teaching_service.prepare(TeachingChatRequest.model_validate(BASE))
    assert mode == "case_guide" and not generate_plan
    assert "一次只问一个问题" in prompt
    assert "贴标签" in prompt and "喧宾夺主" in prompt
    assert l1_labels


def test_original_plan_uses_original_format_mode():
    payload = lesson_payload("请修改原教案中的教学过程")
    payload["metadata"]["originalLessonPlan"] = "# 我原来的标题\n## 教学过程\n原有内容"
    prompt, mode, generate_plan, l1_labels = teaching_service.prepare(TeachingChatRequest.model_validate(payload))
    assert mode == "lesson_plan_assist" and generate_plan
    assert "我原来的标题" in prompt and "优先保留原章节和格式" in prompt


def test_stream_defaults_to_true():
    request = TeachingChatRequest.model_validate({k: v for k, v in BASE.items() if k != "stream"})
    assert request.stream is True


def test_usage_aliases_are_camel_case():
    value = Usage(inputTokens=1, outputTokens=2, totalTokens=3).model_dump(by_alias=True)
    assert value == {"inputTokens": 1, "outputTokens": 2, "totalTokens": 3}


def test_fake_zhipu_result_maps_both_fields():
    class Fake:
        def generate(self, prompt, response_mode, generate_plan=False):
            return ModelResult("# 教案", "已完成教材分析。", "glm-5.3-flash", Usage(inputTokens=10, outputTokens=20, totalTokens=30))
    from app.service import TeachingChatService
    data = TeachingChatService(model_client=Fake()).generate(TeachingChatRequest.model_validate(lesson_payload("请生成教案"))).model_dump(by_alias=True)
    assert data["content"] == "# 教案"
    assert data["reasoning_content"] == "已完成教材分析。"
    assert data["usage"] == {"inputTokens": 10, "outputTokens": 20, "totalTokens": 30}
