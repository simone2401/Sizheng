from __future__ import annotations
import json
from collections.abc import AsyncIterator
from .models import TeachingResponse

def encode(response: TeachingResponse) -> str:
    return f"event: message\ndata: {json.dumps(response.model_dump(by_alias=True), ensure_ascii=False)}\n\n"

async def encode_stream(items: AsyncIterator[TeachingResponse]) -> AsyncIterator[str]:
    async for item in items: yield encode(item)
