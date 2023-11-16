# pylint: disable=duplicate-code
"""
Tests for uwtools.config.formats.ini module.
"""

import filecmp
from typing import Any, Dict

from uwtools.config.formats.sh import SHConfig
from uwtools.tests.support import fixture_path

# Tests


def test_parse_include():
    """
    Test that non-YAML handles include tags properly for bash with no sections.
    """
    cfgobj = SHConfig(fixture_path("include_files.sh"))
    assert cfgobj.get("fruit") == "papaya"
    assert cfgobj.get("how_many") == "17"
    assert cfgobj.get("meat") == "beef"
    assert len(cfgobj) == 5


def test_bash(salad_base, tmp_path):
    """
    Test that bash config load and dump work with a basic bash file.
    """
    infile = fixture_path("simple.sh")
    outfile = tmp_path / "outfile.sh"
    cfgobj = SHConfig(infile)
    expected: Dict[str, Any] = {
        **salad_base["salad"],
        "how_many": "12",
    }
    assert cfgobj == expected
    cfgobj.dump(outfile)
    assert filecmp.cmp(infile, outfile)
    cfgobj.update({"dressing": ["ranch", "italian"]})
    expected["dressing"] = ["ranch", "italian"]
    assert cfgobj == expected
