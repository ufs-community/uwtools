# pylint: disable=missing-function-docstring,protected-access,redefined-outer-name
"""
Tests for uwtools.config.core module.
"""

import datetime
import filecmp
import logging
import sys
from io import StringIO
from unittest.mock import patch

import pytest
import yaml
from pytest import raises

from uwtools import exceptions
from uwtools.config import support, tools
from uwtools.config.formats.yaml import YAMLConfig
from uwtools.exceptions import UWConfigError
from uwtools.logging import log
from uwtools.tests.support import fixture_path, logged
from uwtools.utils.file import FORMAT, _stdinproxy

# Tests


@pytest.mark.parametrize("fmt1", [FORMAT.ini, FORMAT.nml, FORMAT.yaml])
@pytest.mark.parametrize("fmt2", [FORMAT.ini, FORMAT.nml, FORMAT.yaml])
def test_transform_config(fmt1, fmt2, tmp_path):
    """
    Test that transforms config objects to objects of other config subclasses.
    """
    outfile = tmp_path / f"test_{fmt1.lower()}to{fmt2.lower()}_dump.{fmt2}"
    reference = fixture_path(f"simple.{fmt2}")
    cfgin = tools.format_to_config(fmt1)(fixture_path(f"simple.{fmt1}"))
    tools.format_to_config(fmt2).dump_dict(path=outfile, cfg=cfgin.data)
    with open(reference, "r", encoding="utf-8") as f1:
        reflines = [line.strip().replace("'", "") for line in f1]
    with open(outfile, "r", encoding="utf-8") as f2:
        outlines = [line.strip().replace("'", "") for line in f2]
    for line1, line2 in zip(reflines, outlines):
        assert line1 == line2


def test_yaml_config_composite_types():
    """
    Test that YAML load and dump work with a YAML file that has multiple data structures and levels.
    """
    cfgobj = YAMLConfig(fixture_path("result4.yaml"))

    assert cfgobj["step_cycle"] == "PT6H"
    assert isinstance(cfgobj["init_cycle"], datetime.datetime)

    generic_repos = cfgobj["generic_repos"]
    assert isinstance(generic_repos, list)
    assert isinstance(generic_repos[0], dict)
    assert generic_repos[0]["branch"] == "develop"

    models = cfgobj["models"]
    assert models[0]["config"]["vertical_resolution"] == 64


def test_yaml_config_include_files():
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


def test_yaml_config_simple(tmp_path):
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
    with tmpfile.open("w", encoding="utf-8") as f:
        f.write(
            """
foo: {{ bar }}
bar: 2
"""
        )
    with raises(exceptions.UWConfigError) as e:
        YAMLConfig(tmpfile)
    assert "value is enclosed in quotes" in str(e.value)


def test_yaml_constructor_error_unregistered_constructor(tmp_path):
    # Test that unregistered constructor raises UWConfigError.

    tmpfile = tmp_path / "test.yaml"
    with tmpfile.open("w", encoding="utf-8") as f:
        f.write("foo: !not_a_constructor bar")
    with raises(exceptions.UWConfigError) as e:
        YAMLConfig(tmpfile)
    assert "constructor: '!not_a_constructor'" in str(e.value)
    assert "Define the constructor before proceeding" in str(e.value)


# def test_Config___repr__(capsys, nml_cfgobj):
#     print(nml_cfgobj)
#     assert yaml.safe_load(capsys.readouterr().out)["nl"]["n"] == 88


# def test_Config_characterize_values(nml_cfgobj):
#     d = {1: "", 2: None, 3: "{{ n }}", 4: {"a": 88}, 5: [{"b": 99}], 6: "string"}
#     complete, empty, template = nml_cfgobj.characterize_values(values=d, parent="p")
#     assert complete == ["    p4", "    p4.a", "    pb", "    p5", "    p6"]
#     assert empty == ["    p1", "    p2"]
#     assert template == ["    p3: {{ n }}"]


# def test_Config_reify_scalar_str(nml_cfgobj):
#     for x in ["true", "yes", "TRUE"]:
#         assert nml_cfgobj.reify_scalar_str(x) is True
#     for x in ["false", "no", "FALSE"]:
#         assert nml_cfgobj.reify_scalar_str(x) is False
#     assert nml_cfgobj.reify_scalar_str("88") == 88
#     assert nml_cfgobj.reify_scalar_str("'88'") == "88"  # quoted int not converted
#     assert nml_cfgobj.reify_scalar_str("3.14") == 3.14
#     assert nml_cfgobj.reify_scalar_str("NA") == "NA"  # no conversion
#     assert nml_cfgobj.reify_scalar_str("@[foo]") == "@[foo]"  # no conversion for YAML exceptions
#     with raises(AttributeError) as e:
#         nml_cfgobj.reify_scalar_str([1, 2, 3])
#     assert "'list' object has no attribute 'read'" in str(e.value)  # Exception on unintended list


def test_YAMLConfig__load_unexpected_error(tmp_path):
    cfgfile = tmp_path / "cfg.yaml"
    with open(cfgfile, "w", encoding="utf-8") as f:
        print("{n: 88}", file=f)
    with patch.object(yaml, "load") as load:
        msg = "Unexpected error"
        load.side_effect = yaml.constructor.ConstructorError(note=msg)
        with raises(UWConfigError) as e:
            YAMLConfig(config_file=cfgfile)
        assert msg in str(e.value)


def test_YAMLConfig__load_paths_failure_stdin_plus_relpath(caplog):
    # Instantiate a YAMLConfig with no input file, triggering a read from stdin. Patch stdin to
    # provide YAML with an include directive specifying a relative path. Since a relative path
    # is meaningless relative to stdin, assert that an appropriate error is logged and exception
    # raised.
    log.setLevel(logging.INFO)
    _stdinproxy.cache_clear()
    relpath = "../bar/baz.yaml"
    with patch.object(sys, "stdin", new=StringIO(f"foo: {support.INCLUDE_TAG} [{relpath}]")):
        with raises(UWConfigError) as e:
            YAMLConfig()
    msg = f"Reading from stdin, a relative path was encountered: {relpath}"
    assert msg in str(e.value)
    assert logged(caplog, msg)


# Helper functions


# @fixture
# def nml_cfgobj(tmp_path):
#     # Use NMLConfig to exercise methods in Config abstract base class.
#     path = tmp_path / "cfg.nml"
#     with open(path, "w", encoding="utf-8") as f:
#         f.write("&nl n = 88 /")
#     return NMLConfig(config_file=path)
