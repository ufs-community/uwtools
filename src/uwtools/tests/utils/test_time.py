"""
Tests for uwtools.utils.time module.
"""

from datetime import timedelta

from uwtools.utils import time


def test_utils_time_to_datetime(utc):
    expected = utc(2025, 7, 31, 12)
    for value in [utc(2025, 7, 31, 12), "2025-07-31T12:00:00"]:
        assert time.to_datetime(value=value) == expected


def test_utils_time_to_timedelta():
    for value, expected in [
        ("01:02:03", timedelta(hours=1, minutes=2, seconds=3)),
        ("168:00:00", timedelta(days=7)),
    ]:
        assert time.to_timedelta(value=value) == expected
