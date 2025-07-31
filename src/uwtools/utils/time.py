"""
Helpers for working with time values.
"""

from __future__ import annotations

from datetime import datetime


def to_datetime(value: str | datetime) -> datetime:
    if isinstance(value, datetime):
        return value
    return datetime.fromisoformat(value)
