from app.shared.resource_contracts import ResourceResponse


def test_resource_response_contract_validation(resource_client):
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
    assert response.status_code == 200
    parsed = ResourceResponse.model_validate(response.json())
    assert parsed.data_version
    assert parsed.chapter
