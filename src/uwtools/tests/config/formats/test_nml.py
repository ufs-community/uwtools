# pylint: disable=missing-function-docstring,protected-access,redefined-outer-name
"""
Tests for uwtools.config.formats.nml module.
"""

import filecmp
from textwrap import dedent

import f90nml  # type: ignore
from pytest import fixture, mark

from uwtools.config.formats.nml import NMLConfig
from uwtools.tests.support import fixture_path
from uwtools.utils.file import FORMAT

# Fixtures


@fixture
def data():
    return {"nml": {"key": "val"}}


# Tests


def test_nml__get_depth_threshold():
    assert NMLConfig._get_depth_threshold() is None


def test_nml__get_format():
    assert NMLConfig._get_format() == FORMAT.nml


def test_nml__parse_include():
    """
    Test that non-YAML handles include tags properly.
    """
    cfgobj = NMLConfig(fixture_path("include_files.nml"))
    assert cfgobj["config"]["fruit"] == "papaya"
    assert cfgobj["config"]["how_many"] == 17
    assert cfgobj["config"]["meat"] == "beef"
    assert len(cfgobj["config"]) == 5


def test_nml__parse_include_mult_sect():
    """
    Test that non-YAML handles include tags with files that have multiple sections in separate file.
    """
    cfgobj = NMLConfig(fixture_path("include_files_with_sect.nml"))
    assert cfgobj["config"]["fruit"] == "papaya"
    assert cfgobj["config"]["how_many"] == 17
    assert cfgobj["config"]["meat"] == "beef"
    assert cfgobj["config"]["dressing"] == "ranch"
    assert cfgobj["setting"]["size"] == "large"
    assert len(cfgobj["config"]) == 5
    assert len(cfgobj["setting"]) == 3


def test_nml_derived_type_dict():
    nml = NMLConfig(config={"nl": {"o": {"i": 41, "j": 42}}})
    assert nml["nl"]["o"] == {"i": 41, "j": 42}


def test_nml_derived_type_file(tmp_path):
    s = """
    &nl
      o%i = 41
      o%j = 42
    /
    """
    path = tmp_path / "a.nml"
    with open(path, "w", encoding="utf-8") as f:
        print(dedent(s).strip(), file=f)
    nml = NMLConfig(config=path)
    assert nml["nl"]["o"] == {"i": 41, "j": 42}


def test_nml_dump_dict_dict(data, tmp_path):
    path = tmp_path / "a.nml"
    NMLConfig.dump_dict(cfg=data, path=path)
    nml = f90nml.read(path)
    assert nml == data


def test_nml_dump_dict_Namelist(data, tmp_path):
    path = tmp_path / "a.nml"
    NMLConfig.dump_dict(cfg=f90nml.Namelist(data), path=path)
    nml = f90nml.read(path)
    assert nml == data


@mark.parametrize("func", [repr, str])
def test_ini_repr_str(func):
    config = fixture_path("simple.nml")
    with open(config, "r", encoding="utf-8") as f:
        assert func(NMLConfig(config)) == f.read().strip()


def test_nml_simple(salad_base, tmp_path):
    """
    Test that namelist load, update, and dump work with a basic namelist file.
    """
    infile = fixture_path("simple.nml")
    outfile = tmp_path / "outfile.nml"
    cfgobj = NMLConfig(infile)
    expected = salad_base
    expected["salad"]["how_many"] = 12  # must be int for nml
    assert cfgobj == expected
    cfgobj.dump(outfile)
    assert filecmp.cmp(infile, outfile)
    cfgobj.update({"dressing": ["ranch", "italian"]})
    expected["dressing"] = ["ranch", "italian"]
    assert cfgobj == expected
