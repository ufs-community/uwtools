"""
Tests for uwtools.config.formats.ini module.
"""

import filecmp
from typing import Any, Dict

from uwtools.config.formats.ini import INIConfig
from uwtools.tests.support import fixture_path

# Tests


def test_bash(salad_base, tmp_path):
    """
    Test that INI config load and dump work with a basic bash file.
    """
    infile = fixture_path("simple.sh")
    outfile = tmp_path / "outfile.sh"
    cfgobj = INIConfig(infile, space_around_delimiters=False)
    expected: Dict[str, Any] = {
        **salad_base["salad"],
        "how_many": "12",
    }  # str "12" (not int 12) for INI
    assert cfgobj == expected
    cfgobj.dump(outfile)
    assert filecmp.cmp(infile, outfile)
    cfgobj.update({"dressing": ["ranch", "italian"]})
    expected["dressing"] = ["ranch", "italian"]
    assert cfgobj == expected


def test_parse_include():
    """
    Test that non-YAML handles include tags properly for INI with no sections.
    """
    cfgobj = INIConfig(fixture_path("include_files.sh"), space_around_delimiters=False)
    assert cfgobj.get("fruit") == "papaya"
    assert cfgobj.get("how_many") == "17"
    assert cfgobj.get("meat") == "beef"
    assert len(cfgobj) == 5


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
