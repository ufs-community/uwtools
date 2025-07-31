"""
Tests for uwtools.utils.time module.
"""

from datetime import datetime, timezone

from pytest import mark

from uwtools.utils import time


@mark.parametrize(
    "value",
    [
        datetime(2025, 7, 31, 12, tzinfo=timezone.utc).replace(tzinfo=None),
        "2025-07-31T12:00:00",
    ],
)
def test_utils_time_to_datetime(utc, value):
    assert time.to_datetime(value=value) == utc(2025, 7, 31, 12)
