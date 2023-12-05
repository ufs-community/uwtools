# pylint: disable=missing-function-docstring
"""
Tests for uwtools.config.formats.fieldtable module.
"""

from uwtools.config.formats.fieldtable import FieldTableConfig
from uwtools.tests.support import fixture_path

# Tests


def test_simple(tmp_path):
    """
    Test reading a YAML config object and generating a field table file.
    """
    cfgfile = fixture_path("FV3_GFS_v16.yaml")
    outfile = tmp_path / "field_table_from_yaml.FV3_GFS"
    reference = fixture_path("field_table.FV3_GFS_v16")
    FieldTableConfig(cfgfile).dump(outfile)
    with open(reference, "r", encoding="utf-8") as f1:
        reflines = [line.strip().replace("'", "") for line in f1]
    with open(outfile, "r", encoding="utf-8") as f2:
        outlines = [line.strip().replace("'", "") for line in f2]
    for line1, line2 in zip(outlines, reflines):
        assert line1 == line2
