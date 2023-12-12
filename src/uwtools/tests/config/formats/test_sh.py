# pylint: disable=duplicate-code,missing-function-docstring
"""
Tests for uwtools.config.formats.sh module.
"""

import filecmp
from typing import Any, Dict

from pytest import raises

from uwtools.config.formats.sh import SHConfig
from uwtools.exceptions import UWConfigError
from uwtools.tests.support import fixture_path
from uwtools.utils.file import FORMAT

# Tests


def test_get_format():
    assert SHConfig.get_format() == FORMAT.sh


def test_get_depth_threshold():
    assert SHConfig.get_depth_threshold() == 1


def test_instantiation_depth():
    with raises(UWConfigError) as e:
        SHConfig(config={1: {2: {3: 4}}})
    assert str(e.value) == "Cannot instantiate depth-1 SHConfig with depth-3 config"


def test_parse_include():
    """
    Test that an sh file with no sections handles include tags properly.
    """
    cfgobj = SHConfig(fixture_path("include_files.sh"))
    assert cfgobj["fruit"] == "papaya"
    assert cfgobj["how_many"] == "17"
    assert cfgobj["meat"] == "beef"
    assert len(cfgobj) == 5


def test_sh(salad_base, tmp_path):
    """
    Test that sh config load and dump work with a basic sh file.
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
