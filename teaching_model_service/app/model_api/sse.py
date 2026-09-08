from __future__ import annotations
import json
from .models import TeachingResponse

def encode(response: TeachingResponse) -> str:
    return f"event: message\ndata: {json.dumps(response.model_dump(by_alias=True), ensure_ascii=False)}\n\n"
