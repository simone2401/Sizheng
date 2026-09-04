from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, AsyncIterator

import httpx

from app.shared.errors import ModelClientError
from .models import Usage


@dataclass
class ModelResult:
    content: str
    reasoning_content: str
    model: str
    usage: Usage
    finish_reason: str = "stop"


class MockModelClient:
    name = "mock-teaching-model"

    async def generate(self, system_prompt: str, user_prompt: str, response_mode: str, model: str | None = None) -> ModelResult:
        selected_model = model or self.name
        if response_mode == "case_guide":
            content = "我们先看案例中的具体做法。你认为这里的思政内容是在帮助学生理解物理问题，还是暂时脱离了学科主线？"
            reasoning = ""
        else:
            content = "# 课程思政融入初中物理教学\n\n## 《密度的应用》教学设计\n\n## 教学基本信息\n待补充课型、班型与学生基础。\n\n## 教学目标\n学生能够理解并应用密度知识。\n\n## 教学过程\n1. 创设真实情境并提出问题。\n2. 基于教材探究并交流证据。\n\n## 作业与延伸\n完成一个生活中的密度应用任务。"
            reasoning = "已完成教材分析、教案对齐和思政标签匹配；课型、班型与学生基础待补充。"
        usage = Usage(inputTokens=len(prompt), outputTokens=len(content) + len(reasoning), totalTokens=len(prompt) + len(content) + len(reasoning))
        return ModelResult(content, reasoning, selected_model, usage)

    async def stream(self, system_prompt: str, user_prompt: str, response_mode: str, model: str | None = None) -> AsyncIterator[dict[str, Any]]:
        result = await self.generate(system_prompt, user_prompt, response_mode, model)
        if response_mode != "case_guide":
            for chunk in _chunks(result.reasoning_content):
                yield {"content": "", "reasoning_content": chunk, "model": result.model, "finish_reason": None, "usage": None}
        for chunk in _chunks(result.content):
            yield {"content": chunk, "reasoning_content": "", "model": result.model, "finish_reason": None, "usage": None}
        yield {"content": "", "reasoning_content": "", "model": result.model, "finish_reason": "stop", "usage": result.usage}


class ZhipuModelClient:
    url = "https://open.bigmodel.cn/api/paas/v4/chat/completions"

    def __init__(self, api_key: str, model: str = "glm-5.2", timeout: float = 60.0, base_url: str = "https://open.bigmodel.cn/api/paas/v4", client: httpx.AsyncClient | None = None):
        self.api_key, self.default_model, self.timeout = api_key, model, timeout
        self.url = f"{base_url.rstrip('/')}/chat/completions"
        self.client = client or httpx.AsyncClient(timeout=timeout)

    def _headers(self) -> dict[str, str]:
        if not self.api_key:
            raise ModelClientError("MODEL_CONFIGURATION_ERROR", "ZHIPU_API_KEY is not configured")
        return {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}

    @staticmethod
    def _usage(value: dict[str, Any]) -> Usage:
        try:
            return Usage(inputTokens=int(value.get("prompt_tokens", 0)), outputTokens=int(value.get("completion_tokens", 0)), totalTokens=int(value.get("total_tokens", 0)))
        except (TypeError, ValueError) as exc:
            raise ModelClientError("MODEL_RESPONSE_INVALID", "invalid usage in model response") from exc

    def _map_http_error(self, status: int) -> ModelClientError:
        if status == 429:
            return ModelClientError("MODEL_RATE_LIMITED", "upstream model request was rate limited", 429, True)
        return ModelClientError("MODEL_UPSTREAM_ERROR", "upstream model request failed", 502, status >= 500)

    async def generate(self, system_prompt: str, user_prompt: str, response_mode: str, model: str | None = None) -> ModelResult:
        selected_model = model or self.default_model
        messages = _messages(system_prompt, user_prompt)
        try:
            response = await self.client.post(self.url, headers=self._headers(), json={"model": selected_model, "messages": messages, "stream": False}, timeout=self.timeout)
            if response.status_code >= 400: raise self._map_http_error(response.status_code)
            data = response.json()
            choice, message = data["choices"][0], data["choices"][0]["message"]
            content = message.get("content")
            reasoning = message.get("reasoning_content")
            if not isinstance(content, str) or not content.strip() or (reasoning is not None and not isinstance(reasoning, str)): raise ValueError
            return ModelResult(content, reasoning, str(data.get("model", self.default_model)), self._usage(data.get("usage", {})), choice.get("finish_reason", "stop"))
        except ModelClientError: raise
        except httpx.TimeoutException as exc: raise ModelClientError("MODEL_TIMEOUT", "model request timed out", 504, True) from exc
        except httpx.HTTPError as exc: raise ModelClientError("MODEL_NETWORK_ERROR", "model request failed", 502, True) from exc
        except (KeyError, IndexError, TypeError, ValueError, json.JSONDecodeError) as exc: raise ModelClientError("MODEL_RESPONSE_INVALID", "invalid response from model") from exc

    async def stream(self, system_prompt: str, user_prompt: str, response_mode: str, model: str | None = None) -> AsyncIterator[dict[str, Any]]:
        selected_model = model or self.default_model
        messages = _messages(system_prompt, user_prompt)
        try:
            async with self.client.stream("POST", self.url, headers=self._headers(), json={"model": selected_model, "messages": messages, "stream": True}, timeout=self.timeout) as response:
                if response.status_code >= 400: raise self._map_http_error(response.status_code)
                async for line in response.aiter_lines():
                    if not line or not line.startswith("data:"): continue
                    raw = line[5:].strip()
                    if raw == "[DONE]": break
                    try:
                        data = json.loads(raw); choice = data.get("choices", [{}])[0]; delta = choice.get("delta", {})
                        content = delta.get("content", "")
                        reasoning = delta.get("reasoning_content")
                        if not isinstance(content, str) or (reasoning is not None and not isinstance(reasoning, str)): raise ValueError
                        yield {"content": content, "reasoning_content": reasoning, "model": data.get("model", self.default_model), "finish_reason": choice.get("finish_reason"), "usage": self._usage(data["usage"]) if data.get("usage") else None}
                    except (json.JSONDecodeError, KeyError, IndexError, TypeError, ValueError) as exc: raise ModelClientError("MODEL_RESPONSE_INVALID", "invalid streaming response from model") from exc
        except ModelClientError: raise
        except httpx.TimeoutException as exc: raise ModelClientError("MODEL_TIMEOUT", "model request timed out", 504, True) from exc
        except httpx.HTTPError as exc: raise ModelClientError("MODEL_NETWORK_ERROR", "model request failed", 502, True) from exc


def _messages(system_prompt: str, user_prompt: str) -> list[dict[str, str]]:
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]


def _chunks(text: str):
    for index in range(0, len(text), 12):
        yield text[index:index + 12]
