# pylint: disable=duplicate-code
"""
Tests for uwtools.config.formats.sh module.
"""

import filecmp
from typing import Any, Dict

from uwtools.config.formats.sh import SHConfig
from uwtools.tests.support import fixture_path

# Tests


def test_parse_include():
    """
    Test that an sh file with no sections handles include tags properly.
    """
    cfgobj = SHConfig(fixture_path("include_files.sh"))
    assert cfgobj["fruit"] == "papaya"
    assert cfgobj["how_many"] == "17"
    assert cfgobj["meat"] == "beef"
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
