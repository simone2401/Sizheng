from app.resource_api.main import app as resource_app
from app.resource_api.router import service_dependency as resource_service_dependency


def test_invalid_resource_returns_not_found(resource_client):
    response = resource_client.get(
        "/v1/teaching/resources",
        params={
            "schoolLevel": "8年级上",
            "subject": "物理",
            "textbookVersion": "不存在",
            "chapter": "第六章",
            "lesson": "第4节",
        },
    )
    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "RESOURCE_NOT_FOUND"


def test_resource_unavailable_is_structured(resource_client):
    from app.shared.errors import ResourceUnavailableError

    resource_app.dependency_overrides[resource_service_dependency] = lambda: (_ for _ in ()).throw(ResourceUnavailableError())
    response = resource_client.get(
        "/v1/teaching/resources",
        params={
            "schoolLevel": "8年级上",
            "subject": "物理",
            "textbookVersion": "人教版",
            "chapter": "第六章",
            "lesson": "第4节",
        },
    )
    assert response.status_code == 503
    assert response.json()["detail"]["code"] == "RESOURCE_SERVICE_UNAVAILABLE"


def test_static_resource_endpoint_returns_expected_fields(resource_client):
    response = resource_client.get(
        "/v1/teaching/resources/static",
        params={
            "schoolLevel": "8年级上",
            "subject": "物理",
            "textbookVersion": "人教版",
            "chapter": "第六章",
            "lesson": "第4节",
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert isinstance(payload.get("items"), list)
    assert payload["items"]
    first = payload["items"][0]
    assert {"ideologyID", "sourcePage", "ideologyKeyword", "l1_label"}.issubset(first.keys())


def test_resource_endpoint_filters_ideology_paragraphs_by_ideology_ids(resource_client):
    static_response = resource_client.get(
        "/v1/teaching/resources/static",
        params={
            "schoolLevel": "8年级上",
            "subject": "物理",
            "textbookVersion": "人教版",
            "chapter": "第六章",
            "lesson": "第4节",
        },
    )
    ideology_id = static_response.json()["items"][0]["ideologyID"]
    response = resource_client.get(
        "/v1/teaching/resources",
        params={
            "schoolLevel": "8年级上",
            "subject": "物理",
            "textbookVersion": "人教版",
            "chapter": "第六章",
            "lesson": "第4节",
            "ideologyIDs": ideology_id,
        },
    )
    assert response.status_code == 200
    payload = response.json()
    paragraphs = payload.get("ideologyParagraphs", [])
    assert paragraphs
    assert {item["paragraph_id"] for item in paragraphs} == {ideology_id}


def test_static_resource_endpoint_returns_all_paragraphs_for_lesson(resource_client):
    response = resource_client.get(
        "/v1/teaching/resources/static",
        params={
            "schoolLevel": "8年级上",
            "subject": "物理",
            "textbookVersion": "人教版",
            "chapter": "第六章",
            "lesson": "第4节",
        },
    )
    assert response.status_code == 200
    items = response.json()["items"]
    ids = [item["ideologyID"] for item in items]
    assert len(ids) == len(set(ids))
    assert len(ids) == 5
