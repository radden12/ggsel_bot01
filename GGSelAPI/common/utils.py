"""Вспомогательные функции парсинга ответов GGSEL."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional


def as_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def as_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def as_str(value: Any, default: str = "") -> str:
    if value is None:
        return default
    return str(value)


def parse_timestamp(value: Any) -> Optional[datetime]:
    """
    Пытается распарсить отметку времени из ответа площадки.

    Поддерживает unix-время (int/float) и ISO-8601 строки.
    """
    if value is None or value == "":
        return None
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(float(value), tz=timezone.utc)
    text = str(value).strip().replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(text)
    except ValueError:
        return None
