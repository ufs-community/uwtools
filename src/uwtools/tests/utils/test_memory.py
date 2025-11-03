"""
Tests for uwtools.utils.file_helpers module.
"""

from pytest import mark

from uwtools.utils.memory import Memory


@mark.parametrize(
    ("value", "measurement", "expected"),
    [
        ("100MB", "KB", "100000KB"),
        ("100KB", "MB", "0.1MB"),
        ("100GB", "KB", "100000000KB"),
        ("100MB", "GB", "0.1GB"),
        ("100GB", "MB", "100000MB"),
        ("100KB", "GB", "9.999999999999999e-05GB"),
    ],
)
def test_memory_conversions(value, measurement, expected):
    m = Memory(value)
    assert str(m.convert(measurement)) == expected
    assert m.measurement == value[-2:]
