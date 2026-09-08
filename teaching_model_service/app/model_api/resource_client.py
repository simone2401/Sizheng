from __future__ import annotations

from typing import Any

import httpx

from app.shared.auth import bearer_headers
from app.shared.config import ModelSettings
from app.shared.errors import ResourceNotFoundError, ResourceUnavailableError
from app.shared.resource_contracts import ResourceResponse


class ResourceClient:
    def __init__(self, settings: ModelSettings, client: httpx.AsyncClient | None = None):
        self.settings, self.client = settings, client

    async def query(self, **params: Any) -> ResourceResponse:
        clean_params = {key: value for key, value in params.items() if value is not None and value != []}
        if self.client is None:
            raise ResourceUnavailableError("resource client is not initialized")
        try:
            response = await self.client.get(
                f"{self.settings.resource_service_url}/v1/teaching/resources",
                params=clean_params,
                headers=bearer_headers(self.settings.resource_service_api_key),
            )
        except httpx.HTTPError as exc:
            raise ResourceUnavailableError() from exc
        if response.status_code == 404:
            raise ResourceNotFoundError("resource not found")
        if response.status_code in {401, 403}:
            raise ResourceUnavailableError("resource service authentication failed")
        if response.status_code >= 500:
            raise ResourceUnavailableError()
        if response.status_code >= 400:
            raise ResourceUnavailableError("resource request rejected")
        try:
            return ResourceResponse.model_validate(response.json())
        except (ValueError, TypeError) as exc:
            raise ResourceUnavailableError("invalid resource response") from exc
