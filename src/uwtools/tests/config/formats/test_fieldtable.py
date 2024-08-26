# pylint: disable=missing-function-docstring,protected-access,redefined-outer-name
"""
Tests for uwtools.config.formats.fieldtable module.
"""

from pytest import fixture, mark

from uwtools.config.formats.fieldtable import FieldTableConfig
from uwtools.tests.support import fixture_path
from uwtools.utils.file import FORMAT

# Fixtures


@fixture(scope="module")
def config():
    return fixture_path("FV3_GFS_v16.yaml")


@fixture(scope="module")
def ref():
    with open(fixture_path("field_table.FV3_GFS_v16"), "r", encoding="utf-8") as f:
        return f.read().strip()


# Tests


def test_fieldtable__get_depth_threshold():
    assert FieldTableConfig._get_depth_threshold() is None


def test_fieldtable__get_format():
    assert FieldTableConfig._get_format() == FORMAT.fieldtable


def test_fieldtable_instantiation_depth():
    # Any depth is fine.
    assert FieldTableConfig(config={1: {2: {3: 4}}})


@mark.parametrize("func", [repr, str])
def test_fieldtable_repr_str(config, func, ref):
    assert func(FieldTableConfig(config=config)).strip() == ref


def test_fieldtable_simple(config, ref, tmp_path):
    outfile = tmp_path / "field_table_from_yaml.FV3_GFS"
    FieldTableConfig(config=config).dump(outfile)
    with open(outfile, "r", encoding="utf-8") as out:
        assert out.read().strip() == ref
