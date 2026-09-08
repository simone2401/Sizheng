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
