"""
Helpers for working with time values.
"""

from __future__ import annotations

from datetime import datetime, timedelta

ISO8601FMT = "%Y-%m-%dT%H:%M:%S"


def to_datetime(value: str | datetime) -> datetime:
    if isinstance(value, datetime):
        return value
    return datetime.fromisoformat(value)


def to_iso8601(value: str | datetime) -> str:
    return to_datetime(value).strftime(ISO8601FMT)


def to_timedelta(value: int | str | timedelta) -> timedelta:
    if isinstance(value, timedelta):
        return value
    if isinstance(value, int):
        return timedelta(hours=value)
    keys = ["hours", "minutes", "seconds"]
    args = dict(zip(keys, map(int, value.split(":")), strict=False))
    return timedelta(**args)
