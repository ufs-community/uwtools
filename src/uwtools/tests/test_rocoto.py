# pylint: disable=missing-function-docstring
"""
Tests for uwtools.rocoto module.
"""

from uwtools import rocoto

# Test functions


def test_write(tmp_path):
    r = rocoto.RocotoXML()
    r.write(output_dir=tmp_path)
    expected = "<?xml version='1.0' encoding='utf-8'?>\n<workflow>\n</workflow>"
    with open(tmp_path / "contents.xml", "r", encoding="utf-8") as f:
        assert expected == f.read()
