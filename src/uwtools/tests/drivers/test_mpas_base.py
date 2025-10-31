"""
uwtools.drivers.mpas_base tests.
"""

from datetime import datetime, timezone

from pytest import mark

from uwtools.drivers.mpas_base import MPASBase


@mark.parametrize(
    ("interval", "vals"),
    [
        ("1-2-3_04:05:06", [1, 2, 3, 4, 5, 6]),
        ("1-2-3_4:5:6", [1, 2, 3, 4, 5, 6]),
        ("2-3_4:5:6", [0, 2, 3, 4, 5, 6]),
        ("3_4:5:6", [0, 0, 3, 4, 5, 6]),
        ("4:5:6", [0, 0, 0, 4, 5, 6]),
        ("5:6", [0, 0, 0, 0, 5, 6]),
        ("6", [0, 0, 0, 0, 0, 6]),
    ],
)
def test_mpas_base__decode_interval(interval, vals):
    keys = ("years", "months", "days", "hours", "minutes", "seconds")
    assert MPASBase._decode_interval(interval=interval) == dict(zip(keys, vals, strict=True))


def test_mpas_base__decode_timestamp():
    expected = datetime(2025, 5, 7, 15, 6, 1, tzinfo=timezone.utc)
    assert MPASBase._decode_timestamp("2025-05-07_15:06:01") == expected


@mark.parametrize(
    ("expected", "stream"),
    [
        ("1_00:00:00", {"type": "output", "filename_interval": "1_00:00:00"}),
        ("input_interval", {"type": "input;output", "input_interval": "none"}),
        ("output_interval", {"type": "input;output", "input_interval": "initial_only"}),
        ("output_interval", {"type": "output"}),
    ],
)
def test_mpas_base__filename_interval(expected, stream):
    assert MPASBase._filename_interval(stream) == expected
