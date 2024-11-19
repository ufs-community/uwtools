# pylint: disable=missing-function-docstring,protected-access,redefined-outer-name
"""
Tests for uwtools.config.formats.fieldtable module.
"""

from textwrap import dedent

from pytest import fixture, mark

from uwtools.config.formats.fieldtable import FieldTableConfig
from uwtools.tests.support import fixture_path
from uwtools.utils.file import FORMAT

# Fixtures


@fixture(scope="module")
def config():
    return fixture_path("FV3_GFS_v16.yaml")


@fixture
def dumpkit(tmp_path):
    expected = """
    "TRACER", "atmos_mod", "sphum"
               "longname", "specific humidity"
               "units", "kg/kg"
           "profile_type", "fixed", "surface_value=1e+30" /
    """
    d = {
        "sphum": {
            "longname": "specific humidity",
            "units": "kg/kg",
            "profile_type": {"name": "fixed", "surface_value": 1.0e30},
        }
    }
    return d, dedent(expected).strip(), tmp_path / "config.fieldtable"


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


def test_fieldtable_as_dict():
    d1 = {"section": {"key": "value"}}
    config = FieldTableConfig(d1)
    d2 = config.as_dict()
    assert d2 == d1
    assert isinstance(d2, dict)


def test_fieldtable_dump(dumpkit):
    d, expected, path = dumpkit
    FieldTableConfig(d).dump(path)
    with open(path, "r", encoding="utf-8") as f:
        assert f.read().strip() == expected


def test_fieldtable_dump_dict(dumpkit):
    d, expected, path = dumpkit
    FieldTableConfig.dump_dict(d, path=path)
    with open(path, "r", encoding="utf-8") as f:
        assert f.read().strip() == expected
