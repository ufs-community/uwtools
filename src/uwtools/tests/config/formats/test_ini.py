# pylint: disable=missing-function-docstring,protected-access
"""
Tests for uwtools.config.formats.ini module.
"""

import filecmp

from pytest import mark, raises

from uwtools.config.formats.ini import INIConfig
from uwtools.exceptions import UWConfigError
from uwtools.tests.support import fixture_path
from uwtools.utils.file import FORMAT

# Tests


def test_ini__get_depth_threshold():
    assert INIConfig._get_depth_threshold() == 2


def test_ini__get_format():
    assert INIConfig._get_format() == FORMAT.ini


def test_ini_instantiation_depth():
    with raises(UWConfigError) as e:
        INIConfig(config={1: {2: {3: 4}}})
    assert str(e.value) == "Cannot instantiate depth-2 INIConfig with depth-3 config"


def test_ini_parse_include():
    """
    Test that an INI file handles include tags properly.
    """
    cfgobj = INIConfig(fixture_path("include_files.ini"))
    assert cfgobj["config"]["fruit"] == "papaya"
    assert cfgobj["config"]["how_many"] == "17"
    assert cfgobj["config"]["meat"] == "beef"
    assert len(cfgobj["config"]) == 5


@mark.parametrize("func", [repr, str])
def test_ini_repr_str(func):
    config = fixture_path("simple.ini")
    with open(config, "r", encoding="utf-8") as f:
        assert func(INIConfig(config)) == f.read().strip()


def test_ini_simple(salad_base, tmp_path):
    """
    Test that INI config load and dump work with a basic INI file.

    Everything in INI is treated as a string!
    """
    infile = fixture_path("simple.ini")
    outfile = tmp_path / "outfile.ini"
    cfgobj = INIConfig(infile)
    expected = salad_base
    expected["salad"]["how_many"] = "12"  # str "12" (not int 12) for INI
    assert cfgobj == expected
    cfgobj.dump(outfile)
    assert filecmp.cmp(infile, outfile)
    cfgobj.update({"dressing": ["ranch", "italian"]})
    expected["dressing"] = ["ranch", "italian"]
    assert cfgobj == expected
