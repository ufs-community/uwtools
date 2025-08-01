"""
Tests for uwtools.utils.time module.
"""

from datetime import timedelta

from pytest import mark

from uwtools.utils import time


def test_utils_time_to_datetime(utc):
    expected = utc(2025, 7, 31, 12)
    for value in [utc(2025, 7, 31, 12), "2025-07-31T12:00:00"]:
        assert time.to_datetime(value=value) == expected


@mark.parametrize("sep", ["T", " "])
@mark.parametrize("val", ["2025-07-31%s12", "2025-07-31%s12:00", "2025-07-31%s12:00:00"])
def test_utils_time_to_iso8601(sep, val):
    assert time.to_iso8601(val % sep) == "2025-07-31T12:00:00"


def test_utils_time_to_iso8601_dtobj(utc):
    dtobj = utc(2025, 7, 31, 12)
    assert time.to_iso8601(dtobj) == "2025-07-31T12:00:00"


def test_utils_time_to_timedelta():
    for value, expected in [
        ("01:02:03", timedelta(hours=1, minutes=2, seconds=3)),
        ("168:00:00", timedelta(days=7)),
        (6, timedelta(hours=6)),
        (timedelta(seconds=1), timedelta(seconds=1)),
    ]:
        assert time.to_timedelta(value=value) == expected  # type: ignore[arg-type]
