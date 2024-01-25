# pylint: disable=duplicate-code,missing-function-docstring
"""
Tests for uwtools.config.formats.ini module.
"""

import filecmp

from pytest import raises

from uwtools.config.formats.ini import INIConfig
from uwtools.exceptions import UWConfigError
from uwtools.tests.support import fixture_path
from uwtools.utils.file import FORMAT

# Tests


def test_get_format():
    assert INIConfig.get_format() == FORMAT.ini


def test_get_depth_threshold():
    assert INIConfig.get_depth_threshold() == 2


def test_instantiation_depth():
    with raises(UWConfigError) as e:
        INIConfig(config={1: {2: {3: 4}}})
    assert str(e.value) == "Cannot instantiate depth-2 INIConfig with depth-3 config"


def test_parse_include():
    """
    Test that an INI file handles include tags properly.
    """
    cfgobj = INIConfig(fixture_path("include_files.ini"))
    assert cfgobj["config"]["fruit"] == "papaya"
    assert cfgobj["config"]["how_many"] == "17"
    assert cfgobj["config"]["meat"] == "beef"
    assert len(cfgobj["config"]) == 5


def test_simple(salad_base, tmp_path):
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
