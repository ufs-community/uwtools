# pylint: disable=missing-function-docstring,protected-access,redefined-outer-name
"""
Tests for uwtools.config.core module.
"""

import datetime
import filecmp
import logging
import sys
from io import StringIO
from typing import Any, Dict
from unittest.mock import patch

import pytest
import yaml
from pytest import fixture, raises

from uwtools import exceptions
from uwtools.config import support, tools
from uwtools.config.formats.fieldtable import FieldTableConfig
from uwtools.config.formats.ini import INIConfig
from uwtools.config.formats.nml import NMLConfig
from uwtools.config.formats.yaml import YAMLConfig
from uwtools.exceptions import UWConfigError
from uwtools.logging import log
from uwtools.tests.support import fixture_path, logged
from uwtools.utils.file import FORMAT, _stdinproxy, path_if_it_exists

# Test functions


@pytest.mark.parametrize("fmt", [FORMAT.ini, FORMAT.nml, FORMAT.yaml])
def test_compare_config(caplog, fmt, salad_base):
    """
    Compare two config objects.
    """
    log.setLevel(logging.INFO)
    cfgobj = tools.format_to_config(fmt)(fixture_path(f"simple.{fmt}"))
    if fmt == FORMAT.ini:
        salad_base["salad"]["how_many"] = "12"  # str "12" (not int 12) for ini
    assert cfgobj.compare_config(salad_base) is True
    # Expect no differences:
    assert not caplog.records
    caplog.clear()
    # Create differences in base dict:
    salad_base["salad"]["dressing"] = "italian"
    salad_base["salad"]["size"] = "large"
    del salad_base["salad"]["how_many"]
    # assert not cfgobj.compare_config(cfgobj, salad_base)
    assert not cfgobj.compare_config(salad_base)
    # Expect to see the following differences logged:
    for msg in [
        "salad:        how_many:  - 12 + None",
        "salad:        dressing:  - balsamic + italian",
        "salad:            size:  - None + large",
    ]:
        assert logged(caplog, msg)


def test_config_field_table(tmp_path):
    """
    Test reading a YAML config object and generating a field table file.
    """
    cfgfile = fixture_path("FV3_GFS_v16.yaml")
    outfile = tmp_path / "field_table_from_yaml.FV3_GFS"
    reference = fixture_path("field_table.FV3_GFS_v16")
    FieldTableConfig(cfgfile).dump(outfile)
    with open(reference, "r", encoding="utf-8") as f1:
        reflines = [line.strip().replace("'", "") for line in f1]
    with open(outfile, "r", encoding="utf-8") as f2:
        outlines = [line.strip().replace("'", "") for line in f2]
    for line1, line2 in zip(outlines, reflines):
        assert line1 == line2


def test_ini_config_bash(salad_base, tmp_path):
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


def test_ini_config_simple(salad_base, tmp_path):
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


def test_nml_config_simple(salad_base, tmp_path):
    """
    Test that namelist load, update, and dump work with a basic namelist file.
    """
    infile = fixture_path("simple.nml")
    outfile = tmp_path / "outfile.nml"
    cfgobj = NMLConfig(infile)
    expected = salad_base
    expected["salad"]["how_many"] = 12  # must be in for nml
    assert cfgobj == expected
    cfgobj.dump(outfile)
    assert filecmp.cmp(infile, outfile)
    cfgobj.update({"dressing": ["ranch", "italian"]})
    expected["dressing"] = ["ranch", "italian"]
    assert cfgobj == expected


def test_parse_include():
    """
    Test that non-YAML handles include tags properly.
    """
    cfgobj = NMLConfig(fixture_path("include_files.nml"))
    assert cfgobj["config"]["fruit"] == "papaya"
    assert cfgobj["config"]["how_many"] == 17
    assert cfgobj["config"]["meat"] == "beef"
    assert len(cfgobj["config"]) == 5


def test_parse_include_ini():
    """
    Test that non-YAML handles include tags properly for INI with no sections.
    """
    cfgobj = INIConfig(fixture_path("include_files.sh"), space_around_delimiters=False)
    assert cfgobj.get("fruit") == "papaya"
    assert cfgobj.get("how_many") == "17"
    assert cfgobj.get("meat") == "beef"
    assert len(cfgobj) == 5


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


def test_path_if_it_exists(tmp_path):
    """
    Test that function raises an exception when the specified file does not exist, and raises no
    exception when the file exists.
    """

    badfile = tmp_path / "no-such-file"
    with raises(FileNotFoundError):
        path_if_it_exists(badfile)
    goodfile = tmp_path / "exists"
    goodfile.touch()
    assert path_if_it_exists(goodfile)


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


def test_Config___repr__(capsys, nml_cfgobj):
    print(nml_cfgobj)
    assert yaml.safe_load(capsys.readouterr().out)["nl"]["n"] == 88


def test_Config_characterize_values(nml_cfgobj):
    d = {1: "", 2: None, 3: "{{ n }}", 4: {"a": 88}, 5: [{"b": 99}], 6: "string"}
    complete, empty, template = nml_cfgobj.characterize_values(values=d, parent="p")
    assert complete == ["    p4", "    p4.a", "    pb", "    p5", "    p6"]
    assert empty == ["    p1", "    p2"]
    assert template == ["    p3: {{ n }}"]


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


@fixture
def nml_cfgobj(tmp_path):
    # Use NMLConfig to exercise methods in Config abstract base class.
    path = tmp_path / "cfg.nml"
    with open(path, "w", encoding="utf-8") as f:
        f.write("&nl n = 88 /")
    return NMLConfig(config_file=path)


@fixture
def salad_base():
    return {
        "salad": {
            "base": "kale",
            "fruit": "banana",
            "vegetable": "tomato",
            "how_many": 12,
            "dressing": "balsamic",
        }
    }
