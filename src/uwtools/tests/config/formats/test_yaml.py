"""
Tests for uwtools.config.formats.yaml module.
"""

import filecmp
import sys
from collections import OrderedDict
from datetime import datetime, timedelta
from io import StringIO
from textwrap import dedent
from unittest.mock import patch

import f90nml  # type: ignore[import-untyped]
import yaml
from pytest import fixture, mark, raises

from uwtools import exceptions
from uwtools.config import support
from uwtools.config.formats.yaml import YAMLConfig
from uwtools.exceptions import UWConfigError
from uwtools.tests.support import fixture_path
from uwtools.utils.file import FORMAT, _stdinproxy

# Fixtures


@fixture
def dumpkit(tmp_path, utc):
    yaml = """
    section:
      cycle: '2025-07-31T12:00:00'
      leadtime: !timedelta '6:00:00'
    """
    d = {"section": {"cycle": utc(2025, 7, 31, 12), "leadtime": timedelta(seconds=21600)}}
    expected = dedent(yaml).strip()
    path = tmp_path / "config.yaml"
    return d, expected, path


# Tests


def test_yaml__add_yaml_representers():
    YAMLConfig._add_yaml_representers()
    representers = yaml.Dumper.yaml_representers
    for x in [
        OrderedDict,
        datetime,
        f90nml.Namelist,
        support.UWYAMLConvert,
        support.UWYAMLGlob,
        support.UWYAMLRemove,
        timedelta,
    ]:
        assert x in representers


def test_yaml__get_depth_threshold():
    assert YAMLConfig._get_depth_threshold() is None


def test_yaml__get_format():
    assert YAMLConfig._get_format() == FORMAT.yaml


def test_yaml__represent_namelist():
    YAMLConfig._add_yaml_representers()
    namelist = f90nml.reads("&namelist\n key = value\n/\n")
    expected = "{namelist: {key: value}}"
    assert yaml.dump(namelist, default_flow_style=True).strip() == expected


def test_yaml__represent_ordereddict():
    YAMLConfig._add_yaml_representers()
    ordereddict_values = OrderedDict([("example", OrderedDict([("key", "value")]))])
    expected = "{example: {key: value}}"
    assert yaml.dump(ordereddict_values, default_flow_style=True).strip() == expected


def test_yaml_instantiation_depth():
    # Any depth is fine.
    assert YAMLConfig(config={1: {2: {3: 4}}})


def test_yaml_composite_types():
    """
    Test that YAML load and dump work with a YAML file that has multiple data structures and levels.
    """
    cfgobj = YAMLConfig(fixture_path("result4.yaml"))

    assert cfgobj["step_cycle"] == "PT6H"
    assert isinstance(cfgobj["init_cycle"], datetime)

    generic_repos = cfgobj["generic_repos"]
    assert isinstance(generic_repos, list)
    assert isinstance(generic_repos[0], dict)
    assert generic_repos[0]["branch"] == "develop"

    models = cfgobj["models"]
    assert models[0]["config"]["vertical_resolution"] == 64


def test_yaml_include_files():
    """
    Test that including files via the include constructor works as expected.
    """
    cfgobj = YAMLConfig(fixture_path("include_files.yaml"))

    # 1-file include tests.

    assert cfgobj["salad"]["fruit"] == "papaya"
    assert cfgobj["salad"]["how_many"] == 17
    assert len(cfgobj["salad"]) == 4

    # 2-file test, checking that values provided by the first file are replaced
    # by values from the second file. There should be 7 items under two_files.

    assert cfgobj["two_files"]["fruit"] == "papaya"
    assert cfgobj["two_files"]["vegetable"] == "peas"
    assert len(cfgobj["two_files"]) == 7

    # 2-file test, but with included files reversed.

    assert cfgobj["reverse_files"]["vegetable"] == "eggplant"


def test_yaml_simple(tmp_path):
    """
    Test that YAML load, update, and dump work with a basic YAML file.
    """
    infile = fixture_path("simple2.yaml")
    outfile = tmp_path / "outfile.yml"
    cfgobj = YAMLConfig(infile)
    expected = {
        "account": "user_account",
        "extra_stuff": 12345,
        "jobname": "abcd",
        "nodes": 1,
        "queue": "bos",
        "scheduler": "slurm",
        "tasks_per_node": 4,
        "walltime": "00:01:00",
    }
    assert cfgobj == expected
    cfgobj.dump(outfile)
    assert filecmp.cmp(infile, outfile)
    cfgobj.update({"nodes": 12})
    expected["nodes"] = 12
    assert cfgobj == expected


def test_yaml_constructor_error_no_quotes(tmp_path):
    # Test that Jinja2 template without quotes raises UWConfigError.
    tmpfile = tmp_path / "test.yaml"
    s = """
    foo: {{ bar }}
    bar: 2
    """
    tmpfile.write_text(dedent(s).strip())
    with raises(exceptions.UWConfigError) as e:
        YAMLConfig(tmpfile)
    assert "value is enclosed in quotes" in str(e.value)


def test_yaml_constructor_error_not_dict_from_file(tmp_path):
    # Test that a useful exception is raised if the YAML file input is a non-dict value.
    tmpfile = tmp_path / "test.yaml"
    tmpfile.write_text("hello")
    with raises(exceptions.UWConfigError) as e:
        YAMLConfig(tmpfile)
    assert f"Parsed a str value from {tmpfile}, expected a dict" in str(e.value)


def test_yaml_constructor_error_not_dict_from_stdin():
    # Test that a useful exception is raised if the YAML stdin input is a non-dict value.
    with (
        StringIO("42") as sio,
        patch.object(sys, "stdin", new=sio),
        raises(exceptions.UWConfigError) as e,
    ):
        YAMLConfig()
    assert "Parsed an int value from stdin, expected a dict" in str(e.value)


def test_yaml_constructor_error_unregistered_constructor(tmp_path):
    # Test that unregistered constructor raises UWConfigError.

    tmpfile = tmp_path / "test.yaml"
    tmpfile.write_text("foo: !not_a_constructor bar")
    with raises(exceptions.UWConfigError) as e:
        YAMLConfig(tmpfile)
    assert "constructor: '!not_a_constructor'" in str(e.value)
    assert "Define the constructor before proceeding" in str(e.value)


@mark.parametrize("func", [repr, str])
def test_yaml_repr_str(func):
    config = fixture_path("simple.yaml")
    for actual, expected in zip(
        func(YAMLConfig(config)).split("\n"), config.read_text().split("\n")
    ):
        assert actual.strip() == expected.strip()


def test_yaml_stdin_plus_relpath_failure(logged):
    # Instantiate a YAMLConfig with no input file, triggering a read from stdin. Patch stdin to
    # provide YAML with an include directive specifying a relative path. Since a relative path
    # is meaningless relative to stdin, assert that an appropriate error is logged and exception
    # raised.
    _stdinproxy.cache_clear()
    relpath = "../bar/baz.yaml"
    with (
        StringIO(f"foo: {support.INCLUDE_TAG} [{relpath}]") as sio,
        patch.object(sys, "stdin", new=sio),
        raises(UWConfigError) as e,
    ):
        YAMLConfig()
    msg = f"Reading from stdin, a relative path was encountered: {relpath}"
    assert msg in str(e.value)
    assert logged(msg)


def test_yaml_unexpected_error(tmp_path):
    cfgfile = tmp_path / "cfg.yaml"
    cfgfile.write_text("{n: 42}")
    with patch.object(yaml, "load") as load:
        msg = "Unexpected error"
        load.side_effect = yaml.constructor.ConstructorError(note=msg)
        with raises(UWConfigError) as e:
            YAMLConfig(config=cfgfile)
        assert msg in str(e.value)


def test_yaml_as_dict():
    d1 = {"section": {"key": "value"}}
    config = YAMLConfig(d1)
    d2 = config.as_dict()
    assert d2 == d1
    assert isinstance(d2, dict)


def test_yaml_dump(dumpkit):
    d, expected, path = dumpkit
    YAMLConfig(d).dump(path)
    assert path.read_text().strip() == expected


def test_yaml_dump_dict(dumpkit):
    d, expected, path = dumpkit
    YAMLConfig.dump_dict(d, path=path)
    assert path.read_text().strip() == expected
