"""case_diagnosis_card 的输出解析与充分性前缀捕获。

模型侧按分隔符纯文本输出（首行 SUFFICIENT: 0/1 + 四个 === key === 段落），
diagnosisCard 结构化字段由本模块解析拼装——不要求模型直出 JSON
（实测中文正文内未转义半角引号会破坏 JSON，无法靠 prompt 根除）。
"""
from __future__ import annotations

import re

from app.shared.errors import ModelClientError

SLOTS = {
    "common_problem": (
        ("problem", "问题"),
        ("cause", "原因"),
        ("fix", "改法"),
        ("evidence", "学习证据"),
    ),
    "typical_case": (
        ("highlight", "亮点"),
        ("intent", "设计意图"),
        ("transfer", "迁移建议"),
        ("evidence", "学习证据"),
    ),
}
_TYPICAL_KEYS = {"highlight", "intent", "transfer"}

SUFFICIENT_LINE_RE = re.compile(r"^\s*SUFFICIENT\s*[:：]\s*([01])\s*$", re.IGNORECASE)
SUFFICIENT_PREFIX_RE = re.compile(r"SUFFICIENT\s*[:：]\s*([01])", re.IGNORECASE)
MARKER_RE = re.compile(r"^===\s*([a-zA-Z_]+)\s*===$")


def detect_sufficient(accumulated: str) -> int | None:
    """流式过程中从已累积文本前缀尽早捕获 sufficient（模型固定最先输出该行）。"""
    match = SUFFICIENT_PREFIX_RE.search(accumulated)
    return int(match.group(1)) if match else None


def parse_card(raw_text: str) -> dict:
    """把模型的分隔符纯文本解析为 diagnosisCard 对象；任何违规抛 ModelClientError。"""
    def invalid(message: str) -> ModelClientError:
        return ModelClientError("MODEL_FORMAT_VIOLATION", f"诊断卡输出解析失败：{message}", 502, True)

    lines = raw_text.splitlines()
    index = next((i for i, line in enumerate(lines) if line.strip()), None)
    if index is None:
        raise invalid("输出为空")
    first = SUFFICIENT_LINE_RE.match(lines[index])
    if not first:
        raise invalid(f"首行缺少 SUFFICIENT: 0/1，实际首行：{lines[index][:40]!r}")
    sufficient = int(first.group(1))

    found: list[dict] = []
    current: dict | None = None
    for line in lines[index + 1:]:
        marker = MARKER_RE.match(line.strip())
        if marker:
            if current is not None:
                found.append(current)
            current = {"key": marker.group(1).lower(), "body": ""}
        elif current is not None:
            current["body"] += line + "\n"
        elif line.strip():
            raise invalid(f"首个 === 标记前出现多余内容：{line.strip()[:30]!r}")
    if current is not None:
        found.append(current)

    keys = [item["key"] for item in found]
    if not keys:
        raise invalid("未找到任何 === 槽位标记")
    card_type = "typical_case" if any(key in _TYPICAL_KEYS for key in keys) else "common_problem"
    slots = SLOTS[card_type]
    expected = [slot_key for slot_key, _ in slots]
    missing = [key for key in expected if key not in keys]
    if missing:
        raise invalid(f"槽位缺失或为空：{','.join(missing)}；实际标记：{','.join(keys)}")

    by_key = {item["key"]: item["body"].strip() for item in found}
    sections = []
    for slot_key, title in slots:
        body = by_key.get(slot_key, "").strip()
        if not body:
            raise invalid(f"槽位 {slot_key} 正文为空")
        sections.append({"key": slot_key, "title": title, "body": body})
    return {"sufficient": sufficient, "sections": sections}
