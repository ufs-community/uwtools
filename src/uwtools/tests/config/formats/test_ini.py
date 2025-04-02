"""
Tests for uwtools.config.formats.ini module.
"""

import filecmp
from textwrap import dedent

from pytest import fixture, mark, raises

from uwtools.config.formats.ini import INIConfig
from uwtools.exceptions import UWConfigError
from uwtools.tests.support import fixture_path
from uwtools.utils.file import FORMAT

# Fixtures


@fixture
def dumpkit(tmp_path):
    expected = """
    [section]
    key = value
    """
    return {"section": {"key": "value"}}, dedent(expected).strip(), tmp_path / "config.ini"


# Tests


def test_ini__get_depth_threshold():
    assert INIConfig._get_depth_threshold() == 2


def test_ini__get_format():
    assert INIConfig._get_format() == FORMAT.ini


def test_ini__parse_include():
    """
    Test that an INI file handles include tags properly.
    """
    cfgobj = INIConfig(fixture_path("include_files.ini"))
    assert cfgobj["config"]["fruit"] == "papaya"
    assert cfgobj["config"]["how_many"] == "17"
    assert cfgobj["config"]["meat"] == "beef"
    assert len(cfgobj["config"]) == 5


def test_ini_instantiation_depth():
    with raises(UWConfigError) as e:
        INIConfig(config={1: {2: {3: 4}}})
    assert str(e.value) == "Cannot instantiate depth-2 INIConfig with depth-3 config"


@mark.parametrize("func", [repr, str])
def test_ini_repr_str(func):
    config = fixture_path("simple.ini")
    assert func(INIConfig(config)) == config.read_text().strip()


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


def test_ini_as_dict():
    d1 = {"section": {"key": "value"}}
    config = INIConfig(d1)
    d2 = config.as_dict()
    assert d2 == d1
    assert isinstance(d2, dict)


def test_ini_dump(dumpkit):
    d, expected, path = dumpkit
    INIConfig(d).dump(path)
    assert path.read_text().strip() == expected


def test_ini_dump_dict(dumpkit):
    d, expected, path = dumpkit
    INIConfig.dump_dict(d, path=path)
    assert path.read_text().strip() == expected
