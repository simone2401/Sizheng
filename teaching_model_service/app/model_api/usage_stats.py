from __future__ import annotations
import asyncio
import json
import os
from collections import defaultdict
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any

# 统计口径：一次 HTTP 调用记一行（成功记 usage token，失败记 error_code）。
# 时区固定为东八区，按天分组与业务方对账时不受服务器时区影响。
_TZ = timezone(timedelta(hours=8))


class UsageStats:
    def __init__(self, path: str | None = None):
        env_path = os.getenv("USAGE_LOG_PATH")
        self.path = Path(path or env_path or Path(__file__).resolve().parents[2] / "data" / "usage_log.jsonl")
        self._lock = asyncio.Lock()

    def _now(self) -> str:
        return datetime.now(_TZ).isoformat(timespec="seconds")

    async def record(self, **fields: Any) -> None:
        entry = {"ts": self._now(), **fields}
        line = json.dumps(entry, ensure_ascii=False)
        async with self._lock:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with self.path.open("a", encoding="utf-8") as fh:
                fh.write(line + "\n")

    def summary(self, days: int = 30) -> dict[str, Any]:
        if not self.path.exists():
            return {"since": None, "total": self._empty_total(), "by_day": {}, "by_chat_type": {}, "by_model": {}, "by_api_key": {}, "by_client_ip": {}, "by_error": {}}
        cutoff = (datetime.now(_TZ) - timedelta(days=days)).date()
        total = self._empty_total()
        by_day: dict[str, dict[str, int]] = {}
        by_chat_type: dict[str, dict[str, int]] = defaultdict(lambda: self._empty_total())
        by_model: dict[str, dict[str, int]] = defaultdict(lambda: self._empty_total())
        by_api_key: dict[str, dict[str, int]] = defaultdict(lambda: self._empty_total())
        by_client_ip: dict[str, dict[str, int]] = defaultdict(lambda: self._empty_total())
        by_error: dict[str, int] = defaultdict(int)
        since: str | None = None
        with self.path.open(encoding="utf-8") as fh:
            for raw in fh:
                try:
                    entry = json.loads(raw)
                except json.JSONDecodeError:
                    continue
                day = entry.get("ts", "")[:10]
                if not day or datetime.fromisoformat(entry["ts"]).date() < cutoff:
                    continue
                since = day if since is None else min(since, day)
                self._add(total, entry)
                self._add(by_day.setdefault(day, self._empty_total()), entry)
                chat_type = entry.get("chat_type") or "unknown"
                model = entry.get("model") or "unknown"
                api_key = entry.get("api_key") or "unknown"
                client_ip = entry.get("client_ip") or "unknown"
                self._add(by_chat_type[chat_type], entry)
                self._add(by_model[model], entry)
                self._add(by_api_key[api_key], entry)
                self._add(by_client_ip[client_ip], entry)
                if entry.get("status") == "error":
                    by_error[entry.get("error_code") or "UNKNOWN"] += 1
        return {"since": since, "days": days, "total": total, "by_day": dict(sorted(by_day.items())), "by_chat_type": dict(by_chat_type), "by_model": dict(by_model), "by_api_key": dict(by_api_key), "by_client_ip": dict(sorted(by_client_ip.items(), key=lambda kv: -kv[1]["calls"])), "by_error": dict(by_error)}

    @staticmethod
    def _empty_total() -> dict[str, int]:
        return {"calls": 0, "ok": 0, "error": 0, "input_tokens": 0, "output_tokens": 0, "total_tokens": 0}

    @staticmethod
    def _add(bucket: dict[str, int], entry: dict[str, Any]) -> None:
        bucket["calls"] += 1
        if entry.get("status") == "ok":
            bucket["ok"] += 1
            usage = entry.get("usage") or {}
            bucket["input_tokens"] += int(usage.get("input_tokens") or 0)
            bucket["output_tokens"] += int(usage.get("output_tokens") or 0)
            bucket["total_tokens"] += int(usage.get("total_tokens") or 0)
        else:
            bucket["error"] += 1


stats = UsageStats()
