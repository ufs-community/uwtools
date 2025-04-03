"""
Tests for uwtools.config.formats.sh module.
"""

from textwrap import dedent
from typing import Any

from pytest import fixture, mark, raises

from uwtools.config.formats.sh import SHConfig
from uwtools.exceptions import UWConfigError
from uwtools.tests.support import fixture_path
from uwtools.utils.file import FORMAT

# Fixtures


@fixture
def dumpkit(tmp_path):
    expected = """
    key=value
    """
    return {"key": "value"}, dedent(expected).strip(), tmp_path / "config.yaml"


# Tests


def test_sh__get_depth_threshold():
    assert SHConfig._get_depth_threshold() == 1


def test_sh__get_format():
    assert SHConfig._get_format() == FORMAT.sh


def test_sh__parse_include():
    """
    Test that an sh file with no sections handles include tags properly.
    """
    cfgobj = SHConfig(fixture_path("include_files.sh"))
    assert cfgobj["fruit"] == "papaya"
    assert cfgobj["how_many"] == "17"
    assert cfgobj["meat"] == "beef"
    assert len(cfgobj) == 5


def test_sh_instantiation_depth():
    with raises(UWConfigError) as e:
        SHConfig(config={1: {2: {3: 4}}})
    assert str(e.value) == "Cannot instantiate depth-1 SHConfig with depth-3 config"


@mark.parametrize("func", [repr, str])
def test_sh_repr_str(func):
    config = fixture_path("simple.sh")
    expected = """
    base=kale
    fruit=banana
    vegetable=tomato
    how_many=12
    dressing=balsamic
    """
    assert func(SHConfig(config)) == dedent(expected).strip()


def test_sh(salad_base):
    """
    Test that sh config load and dump work with a basic sh file.
    """
    infile = fixture_path("simple.sh")
    cfgobj = SHConfig(infile)
    expected: dict[str, Any] = {
        **salad_base["salad"],
        "how_many": "12",
    }
    assert cfgobj == expected
    cfgobj.update({"dressing": ["ranch", "italian"]})
    expected["dressing"] = ["ranch", "italian"]
    assert cfgobj == expected


def test_sh_as_dict():
    d1 = {"a": 1}
    config = SHConfig(d1)
    d2 = config.as_dict()
    assert d2 == d1
    assert isinstance(d2, dict)


def test_sh_dump(dumpkit):
    d, expected, path = dumpkit
    SHConfig(d).dump(path)
    assert path.read_text().strip() == expected


def test_sh_dump_dict(dumpkit):
    d, expected, path = dumpkit
    SHConfig.dump_dict(d, path=path)
    assert path.read_text().strip() == expected
