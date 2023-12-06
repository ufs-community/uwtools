# pylint: disable=duplicate-code,missing-function-docstring
"""
Tests for uwtools.config.formats.nml module.
"""

import filecmp

from uwtools.config.formats.nml import NMLConfig
from uwtools.tests.support import fixture_path
from uwtools.utils.file import FORMAT

# Tests


def test_format():
    assert NMLConfig.get_format() == FORMAT.nml


def test_parse_include():
    """
    Test that non-YAML handles include tags properly.
    """
    cfgobj = NMLConfig(fixture_path("include_files.nml"))
    assert cfgobj["config"]["fruit"] == "papaya"
    assert cfgobj["config"]["how_many"] == 17
    assert cfgobj["config"]["meat"] == "beef"
    assert len(cfgobj["config"]) == 5


def test_parse_include_mult_sect():
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


def test_simple(salad_base, tmp_path):
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
