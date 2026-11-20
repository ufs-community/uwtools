"""
Helpers for working with time values.
"""

from __future__ import annotations

from datetime import date, datetime, time, timedelta

from uwtools.exceptions import UWConfigError

ISO8601FMT = "%Y-%m-%dT%H:%M:%S"


def to_datetime(value: str | date | datetime) -> datetime:
    if isinstance(value, datetime):
        return value
    if isinstance(value, date):
        return datetime.combine(value, time.min)
    try:
        return datetime.fromisoformat(value).replace(tzinfo=None)
    except ValueError as e:
        msg = "Converting '%s': %s" % (value, str(e))
        raise UWConfigError(msg) from e


def to_iso8601(value: str | date | datetime) -> str:
    return to_datetime(value).strftime(ISO8601FMT)


def to_timedelta(value: int | str | timedelta) -> timedelta:
    if isinstance(value, timedelta):
        return value
    if isinstance(value, (float, int)):
        return timedelta(hours=value)
    keys = ["hours", "minutes", "seconds"]
    args = dict(zip(keys, map(float, value.split(":")), strict=False))
    return timedelta(**args)
