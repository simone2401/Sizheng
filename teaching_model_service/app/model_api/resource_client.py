from __future__ import annotations
import httpx
from typing import Any
from app.shared.auth import bearer_headers
from app.shared.config import ModelSettings
from app.shared.errors import ResourceNotFoundError, ResourceUnavailableError

class ResourceClient:
    def __init__(self, settings: ModelSettings, client: httpx.AsyncClient | None = None): self.settings, self.client = settings, client
    async def query(self, **params: Any) -> dict[str, Any]:
        clean_params = {key: value for key, value in params.items() if value is not None and value != []}
        try:
            response = await self.client.get(
                f"{self.settings.resource_service_url}/v1/teaching/resources",
                params=clean_params,
                headers=bearer_headers(self.settings.resource_service_api_key),
            )
        except httpx.HTTPError as exc: raise ResourceUnavailableError() from exc
        if response.status_code == 404: raise ResourceNotFoundError("resource not found")
        if response.status_code >= 400: raise ResourceUnavailableError()
        try: return response.json()
        except ValueError as exc: raise ResourceUnavailableError("invalid resource response") from exc
