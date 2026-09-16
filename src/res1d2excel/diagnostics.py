"""Runtime diagnostics settings for res1d2excel."""

from __future__ import annotations

from typing import Iterable, Any


_debug_enabled = False
DEFAULT_VALUE_LIMIT = 50


def set_debug(enabled: bool) -> None:
    global _debug_enabled
    _debug_enabled = bool(enabled)


def is_debug() -> bool:
    return _debug_enabled


def format_values(values: Iterable[Any], limit: int = DEFAULT_VALUE_LIMIT) -> str:
    items = list(values)
    shown = items[:limit]
    text = ", ".join(repr(item) for item in shown)
    if len(items) > limit:
        text += f", ... and {len(items) - limit} more"
    return f"[{text}]"
