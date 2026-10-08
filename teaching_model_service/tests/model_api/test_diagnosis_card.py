import asyncio
import json

import pytest
from conftest import BASE, FakeResourceClient

from app.model_api.main import app as model_app
from app.model_api.model_clients import MockModelClient
from app.model_api.models import TeachingChatRequest
from app.model_api.router import service_dependency as model_service_dependency
from app.model_api.router import settings_dependency as model_settings_dependency
from app.model_api.teaching_service import TeachingChatService
from app.shared.config import ModelSettings
from app.shared.errors import ModelClientError
from app.model_api.diagnosis import detect_sufficient, parse_card


def msg(role, text):
    return {"role": role, "content": [{"type": "TEXT", "text": text}]}


def card_payload(history=None, stream=False):
    messages = [msg("USER", "【案例】某教师把密度概念课上成了公式代换训练课，整节课围绕 m=ρV 反复做题。请开始案例学习。")]
    messages.extend(history or [])
    payload = json.loads(json.dumps(BASE))
    payload["stream"] = stream
    payload["messages"] = messages
    payload["metadata"]["chatType"] = "case_diagnosis_card"
    return payload


TWO_ROUND_HISTORY = [
    msg("USER", "我觉得这节课的问题是没有让学生经历概念形成过程。"),
    msg("ASSISTANT", "你说到了探究过程。能再具体说说设计意图层面的问题吗？"),
    msg("USER", "教学目标定位停留在会算而非理解，所以跳过了归纳，这是我判断的依据。"),
    msg("ASSISTANT", "很好，你已经开始用目标定位来审视设计了。"),
]


@pytest.fixture
def card_client():
    service = TeachingChatService(FakeResourceClient(), model_client=MockModelClient())
    settings = ModelSettings("127.0.0.1", 8000, "http://127.0.0.1:8001", "", frozenset(), True, "mock", "", "", "glm-5.3-flash", 60.0, ())
    model_app.dependency_overrides[model_service_dependency] = lambda: service
    model_app.dependency_overrides[model_settings_dependency] = lambda: settings
    from fastapi.testclient import TestClient
    with TestClient(model_app) as client:
        yield client
    model_app.dependency_overrides.clear()


# ---- diagnosis.py 单元：解析与违规 ----

def _raw(card_type):
    keys = {"typical": ("highlight", "intent", "transfer", "evidence"), "common": ("problem", "cause", "fix", "evidence")}[card_type]
    body = "\n".join(f"=== {key} ===\n{key} 的正文内容。" for key in keys)
    return f"SUFFICIENT: 1\n{body}\n"


def test_parse_card_common_problem_slots():
    card = parse_card(_raw("common"))
    assert card["sufficient"] == 1
    assert [s["key"] for s in card["sections"]] == ["problem", "cause", "fix", "evidence"]
    assert [s["title"] for s in card["sections"]] == ["问题", "原因", "改法", "学习证据"]


def test_parse_card_typical_case_slots():
    card = parse_card(_raw("typical"))
    assert [s["key"] for s in card["sections"]] == ["highlight", "intent", "transfer", "evidence"]
    assert [s["title"] for s in card["sections"]] == ["亮点", "设计意图", "迁移建议", "学习证据"]


def test_parse_card_requires_sufficient_first_line():
    with pytest.raises(ModelClientError) as exc:
        parse_card("=== problem ===\n正文")
    assert exc.value.code == "MODEL_FORMAT_VIOLATION" and exc.value.retriable and exc.value.status_code == 502


def test_parse_card_rejects_missing_slot_and_empty_body():
    with pytest.raises(ModelClientError):
        parse_card("SUFFICIENT: 0\n=== problem ===\n正文\n=== cause ===\n正文\n=== fix ===\n正文\n")
    with pytest.raises(ModelClientError):
        parse_card("SUFFICIENT: 0\n=== problem ===\n\n=== cause ===\n正文\n=== fix ===\n正文\n=== evidence ===\n正文\n")


def test_parse_card_rejects_junk_before_first_marker():
    with pytest.raises(ModelClientError):
        parse_card("SUFFICIENT: 0\n多余的一行\n=== problem ===\n正文\n=== cause ===\n正文\n=== fix ===\n正文\n=== evidence ===\n正文\n")


def test_detect_sufficient_captures_prefix():
    assert detect_sufficient("SUFFICIENT: 0\n=== problem") == 0
    assert detect_sufficient("SUFFICIENT:1\n") == 1
    assert detect_sufficient("SUFFIC") is None


# ---- 服务级：mock 客户端（content 恒空、卡片由 diagnosisCard 承载） ----

def test_generate_card_zero_rounds_sufficient_zero():
    service = TeachingChatService(FakeResourceClient(), model_client=MockModelClient())
    request = TeachingChatRequest.model_validate(card_payload())
    response = asyncio.run(_generate(service, request))
    assert response.content == ""
    assert response.diagnosis_card["sufficient"] == 0
    sections = response.diagnosis_card["sections"]
    assert len(sections) == 4 and sections[3]["key"] == "evidence"
    assert sections[3]["body"].startswith("（暂缺）")


async def _generate(service, request):
    return await service.generate(await service.prepare(request))


def test_generate_card_two_rounds_sufficient_one_quotes_teacher():
    service = TeachingChatService(FakeResourceClient(), model_client=MockModelClient())
    request = TeachingChatRequest.model_validate(card_payload(history=TWO_ROUND_HISTORY))
    response = asyncio.run(_generate(service, request))
    assert response.diagnosis_card["sufficient"] == 1
    assert "对话中提到" in response.diagnosis_card["sections"][3]["body"]


def test_stream_card_exactly_two_business_frames():
    service = TeachingChatService(FakeResourceClient(), model_client=MockModelClient())

    async def run():
        events = []
        async for event in service.stream(await service.prepare(TeachingChatRequest.model_validate(card_payload(history=TWO_ROUND_HISTORY)))):
            events.append(event)
        return events

    events = asyncio.run(run())
    card_events = [e for e in events if e.diagnosis_card is not None]
    assert len(card_events) == 2, "两段式：应恰有首分片与终止分片两个业务帧"
    assert all(e.content == "" for e in events), "content 恒为空"
    first, terminal = card_events
    assert first.diagnosis_card["sufficient"] == 1 and first.diagnosis_card["sections"] is None
    assert first.finish_reason is None
    assert terminal.diagnosis_card["sections"] is not None and len(terminal.diagnosis_card["sections"]) == 4
    assert terminal.finish_reason == "stop"


# ---- 路由级 ----

def test_route_card_nonstream(card_client):
    data = card_client.post("/v1/chat/teaching", json=card_payload(history=TWO_ROUND_HISTORY, stream=False), headers={"Authorization": "Bearer x"}).json()
    assert data["content"] == ""
    assert data["diagnosisCard"]["sufficient"] == 1
    assert [s["key"] for s in data["diagnosisCard"]["sections"]] == ["problem", "cause", "fix", "evidence"]


def test_route_card_stream_two_phase(card_client):
    with card_client.stream("POST", "/v1/chat/teaching", json=card_payload(stream=True), headers={"Authorization": "Bearer x"}) as response:
        events = [json.loads(line[5:]) for line in response.iter_lines() if line.startswith("data:")]
    card_events = [e for e in events if e.get("diagnosisCard") is not None]
    assert len(card_events) == 2
    assert card_events[0]["diagnosisCard"]["sections"] is None
    assert card_events[0]["diagnosisCard"]["sufficient"] == 0  # 无历史 → mock 判 0
    terminal = [e for e in events if e.get("finishReason") == "stop"][0]
    assert terminal["diagnosisCard"]["sections"] is not None
    assert all(e.get("content", "") == "" for e in events)


def test_route_card_allows_assistant_last_message(card_client):
    history = TWO_ROUND_HISTORY + [msg("ASSISTANT", "教师已退出学习，历史快照末条为 ASSISTANT 也应放行。")]
    response = card_client.post("/v1/chat/teaching", json=card_payload(history=history, stream=False), headers={"Authorization": "Bearer x"})
    assert response.status_code == 200


def test_route_dialogue_types_still_require_user_last(model_client):
    client, _, _ = model_client
    payload = json.loads(json.dumps(BASE))
    payload["stream"] = False
    payload["messages"].append(msg("ASSISTANT", "末条不是 USER 应被拒绝"))
    response = client.post("/v1/chat/teaching", json=payload, headers={"Authorization": "Bearer x"})
    assert response.status_code == 400


def test_route_old_types_have_no_diagnosis_card(model_client):
    client, _, _ = model_client
    payload = json.loads(json.dumps(BASE))
    payload["stream"] = False
    data = client.post("/v1/chat/teaching", json=payload, headers={"Authorization": "Bearer x"}).json()
    assert data["diagnosisCard"] is None


def test_route_card_format_violation_returns_502(model_client):
    # conftest 的 FakeModelClient 对 diagnosis_card 模式返回教案文本（无 SUFFICIENT 首行）→ 解析违规
    client, _, _ = model_client
    response = client.post("/v1/chat/teaching", json=card_payload(stream=False), headers={"Authorization": "Bearer x"})
    assert response.status_code == 502
    data = response.json()
    assert data["error"]["code"] == "MODEL_FORMAT_VIOLATION" and data["error"]["retriable"] is True
    assert data["diagnosisCard"] is None and data["finishReason"] == "error"
