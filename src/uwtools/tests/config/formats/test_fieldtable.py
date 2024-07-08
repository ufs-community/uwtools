# pylint: disable=missing-function-docstring,redefined-outer-name
"""
Tests for uwtools.config.formats.fieldtable module.
"""

from pytest import fixture

from uwtools.config.formats.fieldtable import FieldTableConfig
from uwtools.tests.support import fixture_path
from uwtools.utils.file import FORMAT

# Tests


@fixture(scope="module")
def config():
    return fixture_path("FV3_GFS_v16.yaml")


@fixture(scope="module")
def ref():
    with open(fixture_path("field_table.FV3_GFS_v16"), "r", encoding="utf-8") as f:
        return f.read().strip()


def test_fieldtable_get_format():
    assert FieldTableConfig.get_format() == FORMAT.fieldtable


def test_fieldtable_get_depth_threshold():
    assert FieldTableConfig.get_depth_threshold() is None


def test_fieldtable_instantiation_depth():
    # Any depth is fine.
    assert FieldTableConfig(config={1: {2: {3: 4}}})


def test_fieldtable_repr(config, ref):
    assert repr(FieldTableConfig(config=config)).strip() == ref


def test_fieldtable_simple(config, ref, tmp_path):
    outfile = tmp_path / "field_table_from_yaml.FV3_GFS"
    FieldTableConfig(config=config).dump(outfile)
    with open(outfile, "r", encoding="utf-8") as out:
        assert out.read().strip() == ref


def test_fieldtable_str(config, ref):
    assert str(FieldTableConfig(config=config)).strip() == ref
