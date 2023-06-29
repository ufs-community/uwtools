# pylint: disable=duplicate-code,missing-function-docstring

"""
Set of test for loading YAML files using the function call load_yaml
"""
import argparse
import datetime
import filecmp
import io
import itertools
import json
import os
import pathlib
import re
import tempfile
from collections import OrderedDict
from contextlib import redirect_stdout
from textwrap import dedent
from typing import Any, Dict

import pytest

from uwtools import config, exceptions, logger
from uwtools.cli.set_config import parse_args as parse_config_args
from uwtools.test.support import compare_files, fixture_path, line_in_lines
from uwtools.utils import cli_helpers

uwtools_file_base = os.path.join(os.path.dirname(__file__))


@pytest.mark.skip()
def test_parse_include():
    """Test that non-YAML handles !INCLUDE Tags properly"""

    test_nml = os.path.join(uwtools_file_base, pathlib.Path("fixtures/include_files.nml"))
    cfg = config.F90Config(test_nml)

    # salad key tests loading one file.
    assert cfg["config"].get("fruit") == "papaya"
    assert cfg["config"].get("how_many") == 17
    assert cfg["config"].get("meat") == "beef"
    assert len(cfg["config"]) == 5


@pytest.mark.skip()
def test_parse_include_mult_sect():
    """Test that non-YAML handles !INCLUDE tags with files that have
    multiple sections in separate file."""

    test_nml = os.path.join(uwtools_file_base, pathlib.Path("fixtures/include_files_with_sect.nml"))
    cfg = config.F90Config(test_nml)

    # salad key tests loading one file.
    assert cfg["config"].get("fruit") == "papaya"
    assert cfg["config"].get("how_many") == 17
    assert cfg["config"].get("meat") == "beef"
    assert cfg["config"].get("dressing") == "ranch"
    assert cfg["setting"].get("size") == "large"
    assert len(cfg["config"]) == 5
    assert len(cfg["setting"]) == 3


@pytest.mark.skip()
def test_parse_include_ini():
    """Test that non-YAML handles !INCLUDE Tags properly for INI with no
    sections"""

    test_file = os.path.join(uwtools_file_base, pathlib.Path("fixtures/include_files.sh"))
    cfg = config.INIConfig(test_file, space_around_delimiters=False)

    # salad key tests loading one file.
    assert cfg.get("fruit") == "papaya"
    assert cfg.get("how_many") == "17"
    assert cfg.get("meat") == "beef"
    assert len(cfg) == 5


@pytest.mark.skip()
def test_yaml_config_simple():
    """Test that YAML load, update, and dump work with a basic YAML file."""

    test_yaml = os.path.join(uwtools_file_base, pathlib.Path("fixtures/simple2.yaml"))
    cfg = config.YAMLConfig(test_yaml)

    expected = {
        "scheduler": "slurm",
        "jobname": "abcd",
        "extra_stuff": 12345,
        "account": "user_account",
        "nodes": 1,
        "queue": "bos",
        "tasks_per_node": 4,
        "walltime": "00:01:00",
    }
    assert cfg == expected
    assert repr(cfg.data) == json.dumps(expected).replace('"', "'")

    with tempfile.TemporaryDirectory(dir=".") as tmp_dir:
        out_file = f"{tmp_dir}/test_yaml_dump.yml"
        cfg.dump_file(out_file)
        assert filecmp.cmp(test_yaml, out_file)

    cfg.update({"nodes": 12})
    expected["nodes"] = 12

    assert cfg == expected


@pytest.mark.skip()
def test_yaml_config_composite_types():
    """Test that YAML load and dump work with a YAML file that has
    multiple data structures and levels."""

    test_yaml = os.path.join(uwtools_file_base, pathlib.Path("fixtures/result4.yaml"))
    cfg = config.YAMLConfig(test_yaml)

    assert cfg.get("step_cycle") == "PT6H"
    assert isinstance(cfg.get("init_cycle"), datetime.datetime)

    generic_repos = cfg.get("generic_repos")
    assert isinstance(generic_repos, list)
    assert isinstance(generic_repos[0], dict)
    assert generic_repos[0].get("branch") == "develop"

    models = cfg["models"]
    assert models[0].get("config").get("vertical_resolution") == 64


@pytest.mark.skip()
def test_yaml_config_include_files():
    """Test that including files via the !INCLUDE constructor works as
    expected."""

    test_yaml = os.path.join(uwtools_file_base, pathlib.Path("fixtures/include_files.yaml"))
    cfg = config.YAMLConfig(test_yaml)

    # salad key tests loading one file. there should be 4 items under salad
    assert cfg["salad"].get("fruit") == "papaya"
    assert cfg["salad"].get("how_many") == 17
    assert len(cfg["salad"]) == 4

    # two_files key tests loading a list of files, and that values are updated
    # to the last read in. There should be 7 items under two_files
    assert cfg["two_files"].get("fruit") == "papaya"
    assert cfg["two_files"].get("vegetable") == "peas"
    assert len(cfg["two_files"]) == 7

    # reverse_files tests loading a list of files in the reverse order as above,
    # and that the values are updated to the last read in.
    assert cfg["reverse_files"].get("vegetable") == "eggplant"


@pytest.mark.skip()
def test_f90nml_config_simple():
    """Test that f90nml load, update, and dump work with a basic f90 namelist file."""

    test_nml = os.path.join(uwtools_file_base, pathlib.Path("fixtures/simple.nml"))
    cfg = config.F90Config(test_nml)

    expected: Dict[str, Any] = {
        "salad": OrderedDict(
            {
                "base": "kale",
                "fruit": "banana",
                "vegetable": "tomato",
                "how_many": 12,
                "dressing": "balsamic",
            }
        )
    }
    assert cfg == expected

    with tempfile.TemporaryDirectory(dir=".") as tmp_dir:
        out_file = f"{tmp_dir}/test_nml_dump.nml"
        cfg.dump_file(out_file)

        assert filecmp.cmp(test_nml, out_file)

    cfg.update({"dressing": ["ranch", "italian"]})
    expected["dressing"] = ["ranch", "italian"]

    assert cfg == expected


@pytest.mark.skip()
def test_ini_config_simple():
    """Test that INI config load and dump work with a basic INI file.
    Everything in INI is treated as a string!
    """

    test_ini = os.path.join(uwtools_file_base, pathlib.Path("fixtures/simple.ini"))
    cfg = config.INIConfig(test_ini)

    expected: Dict[str, Any] = {
        "salad": {
            "base": "kale",
            "fruit": "banana",
            "vegetable": "tomato",
            "how_many": "12",
            "dressing": "balsamic",
        }
    }
    assert cfg == expected

    with tempfile.TemporaryDirectory(dir=".") as tmp_dir:
        out_file = f"{tmp_dir}/test_ini_dump.ini"
        cfg.dump_file(out_file)

        assert filecmp.cmp(test_ini, out_file)

    cfg.update({"dressing": ["ranch", "italian"]})
    expected["dressing"] = ["ranch", "italian"]
    assert cfg == expected


@pytest.mark.skip()
def test_ini_config_bash():
    """Test that INI config load and dump work with a basic bash file."""

    test_bash = os.path.join(uwtools_file_base, pathlib.Path("fixtures/simple.sh"))
    cfg = config.INIConfig(test_bash, space_around_delimiters=False)

    expected: Dict[str, Any] = {
        "base": "kale",
        "fruit": "banana",
        "vegetable": "tomato",
        "how_many": "12",
        "dressing": "balsamic",
    }
    assert cfg == expected

    with tempfile.TemporaryDirectory(dir=".") as tmp_dir:
        out_file = f"{tmp_dir}/test_bash_dump.sh"
        cfg.dump_file(out_file)

        assert filecmp.cmp(test_bash, out_file)

    cfg.update({"dressing": ["ranch", "italian"]})
    expected["dressing"] = ["ranch", "italian"]
    assert cfg == expected


@pytest.mark.skip()
def test_transform_config():
    """Test that transforms config objects to objects of other config subclasses."""
    # Use itertools to iterate through unique pairs of config subcasses
    # the transforms here ensure consistent file subscripts and config calls
    for test1, test2 in itertools.permutations(["INI", "YAML", "F90"], 2):
        test1file = "NML" if test1 == "F90" else test1
        test2file = "NML" if test2 == "F90" else test2

        test = os.path.join(
            uwtools_file_base, pathlib.Path("fixtures", f"simple.{test1file.lower()}")
        )
        ref = os.path.join(
            uwtools_file_base, pathlib.Path("fixtures", f"simple.{test2file.lower()}")
        )

        cfgin = getattr(config, f"{test1}Config")(test)
        cfgout = getattr(config, f"{test2}Config")()
        cfgout.update(cfgin.data)

        with tempfile.TemporaryDirectory(dir=".") as tmp_dir:
            out_file = f"{tmp_dir}/test_{test1.lower()}to{test2.lower()}_dump.{test2file.lower()}"
            cfgout.dump_file(out_file)

            with open(ref, "r", encoding="utf-8") as f1, open(
                out_file, "r", encoding="utf-8"
            ) as f2:
                reflist = [line.rstrip("\n").strip().replace("'", "") for line in f1]
                outlist = [line.rstrip("\n").strip().replace("'", "") for line in f2]
                lines = zip(reflist, outlist)
                for line1, line2 in lines:
                    assert line1 in line2


@pytest.mark.skip()
def test_config_field_table():
    """Test reading a YAML config object and generating a field file table."""
    config_file = os.path.join(uwtools_file_base, pathlib.Path("fixtures", "FV3_GFS_v16.yaml"))
    expected_file = os.path.join(
        uwtools_file_base, pathlib.Path("fixtures", "field_table.FV3_GFS_v16")
    )

    with tempfile.TemporaryDirectory(dir=".") as tmp_dir:
        out_file = f"{tmp_dir}/field_table_from_yaml.FV3_GFS"

        outcfg = config.FieldTableConfig(config_file)
        outcfg.dump_file(out_file)

        with open(expected_file, "r", encoding="utf-8") as f1, open(
            out_file, "r", encoding="utf-8"
        ) as f2:
            reflist = [line.rstrip("\n").strip().replace("'", "") for line in f1]
            outlist = [line.rstrip("\n").strip().replace("'", "") for line in f2]
            lines = zip(outlist, reflist)
            for line1, line2 in lines:
                assert line1 in line2


@pytest.mark.skip()
def test_dereference():
    """Test that the Jinja2 fields are filled in as expected."""

    os.environ["UFSEXEC"] = "/my/path/"

    test_yaml = os.path.join(uwtools_file_base, pathlib.Path("fixtures/gfs.yaml"))
    cfg = config.YAMLConfig(test_yaml)
    cfg.dereference_all()

    # Check that existing dicts remain
    assert isinstance(cfg["fcst"], dict)
    assert isinstance(cfg["grid_stats"], dict)

    # Check references to other items at same level, and order doesn't
    # matter
    assert cfg["testupdate"] == "testpassed"

    # Check references to other section items
    assert cfg["grid_stats"]["ref_fcst"] == 64

    # Check environment values are included
    assert cfg["executable"] == "/my/path/"

    # Check that env variables that are not defined do not change
    assert cfg["undefined_env"] == "{{ NOPE }}"

    # Check undefined are left as-is
    assert cfg["datapath"] == "{{ [experiment_dir, current_cycle] | path_join }}"

    # Check math
    assert cfg["grid_stats"]["total_points"] == 640000
    assert cfg["grid_stats"]["total_ens_points"] == 19200000

    # Check that statements expand
    assert cfg["fcst"]["output_hours"] == "0 3 6 9 "

    # Check that order isn't a problem
    assert cfg["grid_stats"]["points_per_level"] == 10000


@pytest.mark.skip()
def test_dereference_exceptions(caplog):
    """Test that dereference handles some standard mistakes."""

    log = logger.Logger(name="test_dereference", level="DEBUG")
    cfg = config.YAMLConfig(log_name=log.name)
    cfg.update({"undefined_filter": "{{ 34 | im_not_a_filter }}"})

    with pytest.raises(exceptions.UWConfigError) as e_info:
        cfg.dereference()

    assert "filter: 'im_not_a_filter'" in repr(e_info)
    cfg.pop("undefined_filter", None)

    cfg.update(
        {
            "foo": "bar",
            "soap": "{{ foo }}",
            "num": 2,
            "nada": 0,
            "divide": "{{ num // nada }}",  # ZeroDivisionError
            "list_a": [1, 2, 4],
            "type_prob": '{{ list_a / "a" }}',  # TypeError
        }
    )
    caplog.clear()
    cfg.dereference()

    raised = [rec.msg for rec in caplog.records if "raised" in rec.msg]

    assert "ZeroDivisionError" in raised[0]
    assert "TypeError" in raised[1]


@pytest.mark.skip()
def test_yaml_constructor_errors():
    """When loading YAML with Jinja2 templated values, we see a few
    different renditions of constructor errors. Make sure those are
    clear and helpful."""

    # Test unregistered constructor raises UWConfigError
    cfg = dedent(
        """\
    foo: !not_a_constructor bar
    """
    )

    with tempfile.NamedTemporaryFile(dir="./", mode="w+t") as tmpfile:
        tmpfile.writelines(cfg)
        tmpfile.seek(0)

        with pytest.raises(exceptions.UWConfigError) as e_info:
            config.YAMLConfig(tmpfile.name)
            assert "constructor: !not_a_constructor" in repr(e_info)
            assert "Define the constructor before proceeding" in repr(e_info)

    # Test Jinja2 template without quotes raises UWConfigError
    cfg = dedent(
        """\
    foo: {{ bar }}
    bar: 2
    """
    )

    with tempfile.NamedTemporaryFile(dir="./", mode="w+t") as tmpfile:
        tmpfile.writelines(cfg)
        tmpfile.seek(0)

        with pytest.raises(exceptions.UWConfigError) as e_info:
            config.YAMLConfig(tmpfile.name)
            assert "value is included in quotes" in repr(e_info)


@pytest.mark.skip()
def test_compare_config(caplog):
    """Compare two config objects using method"""
    for user in ["INI", "YAML", "F90"]:
        userfile = "NML" if user == "F90" else user

        basefile = {
            "salad": {
                "base": "kale",
                "fruit": "banana",
                "vegetable": "tomato",
                "how_many": "12",
                "dressing": "balsamic",
            }
        }
        expected = """salad:        dressing:  - italian + balsamic
salad:            size:  - large + None
salad:        how_many:  - None + 12
"""

        noint = "salad:        how_many:  - 12 + 12"

        print(f"Comparing config of base and {user}...")

        log_name = "compare_config"
        logger.Logger(name=log_name, fmt="%(message)s")
        userpath = os.path.join(
            uwtools_file_base, pathlib.Path("fixtures", f"simple.{userfile.lower()}")
        )
        cfguserrun = getattr(config, f"{user}Config")(userpath, log_name=log_name)

        # Capture stdout to validate comparison
        caplog.clear()
        cfguserrun.compare_config(cfguserrun, basefile)

        if caplog.records:
            assert caplog.records[0].msg in noint
        else:
            assert caplog.records == []

        # update base dict to validate differences
        basefile["salad"]["dressing"] = "italian"
        del basefile["salad"]["how_many"]
        basefile["salad"]["size"] = "large"

        caplog.clear()
        cfguserrun.compare_config(cfguserrun, basefile)

        for item in caplog.records:
            assert item.msg in expected


@pytest.mark.skip()
def test_dictionary_depth():
    """Test that the proper dictionary depth is being returned for each file type."""

    input_yaml = os.path.join(uwtools_file_base, pathlib.Path("fixtures/FV3_GFS_v16.yaml"))
    config_obj: config.Config = config.YAMLConfig(input_yaml)
    depth = config_obj.dictionary_depth(config_obj.data)
    assert 3 == depth

    input_nml = os.path.join(uwtools_file_base, pathlib.Path("fixtures/simple.nml"))
    config_obj = config.F90Config(input_nml)
    depth = config_obj.dictionary_depth(config_obj.data)
    assert 2 == depth

    input_ini = os.path.join(uwtools_file_base, pathlib.Path("fixtures/simple2.ini"))
    config_obj = config.INIConfig(input_ini)
    depth = config_obj.dictionary_depth(config_obj.data)
    assert 2 == depth


uwtools_file_base = os.path.join(os.path.dirname(__file__))


@pytest.mark.skip()
def test_path_if_file_exists():
    """Make sure the function works as expected.  It is used as a type in
    argparse, so raises an argparse exception when the user provides a
    non-existant path."""

    with tempfile.NamedTemporaryFile(dir=".", mode="w") as tmp_file:
        assert cli_helpers.path_if_file_exists(tmp_file.name)

    with pytest.raises(argparse.ArgumentTypeError):
        not_a_filepath = "./no_way_this_file_exists.nope"
        cli_helpers.path_if_file_exists(not_a_filepath)


@pytest.mark.skip()
def test_set_config_yaml_simple():
    """Test that providing a YAML base file with necessary settings
    will create a YAML config file"""

    input_file = os.path.join(uwtools_file_base, pathlib.Path("fixtures/simple2.yaml"))

    with tempfile.TemporaryDirectory(dir=".") as tmp_dir:
        out_file = f"{tmp_dir}/test_config_from_yaml.yaml"
        args = ["-i", input_file, "-o", out_file]

        config.create_config_obj(args)

        expected = config.YAMLConfig(input_file)
        expected_file = f"{tmp_dir}/expected_yaml.yaml"
        expected.dump_file(expected_file)

        assert compare_files(expected_file, out_file)


@pytest.mark.skip()
def test_set_config_ini_simple():
    """Test that providing a basic INI file with necessary settings
    will create an INI config file"""

    input_file = os.path.join(uwtools_file_base, pathlib.Path("fixtures/simple.ini"))

    with tempfile.TemporaryDirectory(dir=".") as tmp_dr:
        out_file = f"{tmp_dr}/test_config_from_ini.ini"
        args = ["-i", input_file, "-o", out_file]

        config.create_config_obj(args)

        expected = config.INIConfig(input_file)
        expected_file = f"{tmp_dr}/expected_ini.ini"
        expected.dump_file(expected_file)

        assert compare_files(expected_file, out_file)


@pytest.mark.skip()
def test_set_config_f90nml_simple():
    """Test that providing basic f90nml file with necessary settings
    will create f90nml config file"""

    input_file = os.path.join(uwtools_file_base, pathlib.Path("fixtures/simple.nml"))

    with tempfile.TemporaryDirectory(dir=".") as tmp_dr:
        out_file = f"{tmp_dr}/test_config_from_nml.nml"
        args = ["-i", input_file, "-o", out_file]

        config.create_config_obj(args)

        expected = config.F90Config(input_file)
        expected_file = f"{tmp_dr}/expected_nml.nml"
        expected.dump_file(expected_file)

        assert compare_files(expected_file, out_file)


@pytest.mark.skip()
def test_set_config_bash_simple():
    """Test that providing bash file with necessary settings will
    create an INI config file"""

    input_file = os.path.join(uwtools_file_base, pathlib.Path("fixtures/simple.sh"))

    with tempfile.TemporaryDirectory(dir=".") as tmp_dr:
        out_file = f"{tmp_dr}/test_config_from_bash.ini"

        args = ["-i", input_file, "-o", out_file]

        config.create_config_obj(args)

        expected = config.INIConfig(input_file)
        expected_file = f"{tmp_dr}/expected_ini.ini"
        expected.dump_file(expected_file)

        assert compare_files(expected_file, out_file)


@pytest.mark.skip()
def test_set_config_yaml_config_file():
    """Test that providing a yaml base input file and a config file will
    create and update yaml config file"""

    input_file = os.path.join(uwtools_file_base, pathlib.Path("fixtures/fruit_config.yaml"))
    config_file = os.path.join(
        uwtools_file_base, pathlib.Path("fixtures/fruit_config_similar.yaml")
    )

    with tempfile.TemporaryDirectory(dir=".") as tmp_dir:
        out_file = f"{tmp_dir}/test_config_from_yaml.yaml"
        args = ["-i", input_file, "-o", out_file, "-c", config_file]

        config.create_config_obj(args)

        expected = config.YAMLConfig(input_file)
        config_file_obj = config.YAMLConfig(config_file)
        expected.update_values(config_file_obj)
        expected_file = f"{tmp_dir}/expected_yaml.yaml"
        expected.dump_file(expected_file)

        assert compare_files(expected_file, out_file)


@pytest.mark.skip()
def test_set_config_f90nml_config_file():
    """Test that providing a F90nml base input file and a config file will
    create and update F90nml config file"""

    input_file = os.path.join(uwtools_file_base, pathlib.Path("fixtures/simple.nml"))
    config_file = os.path.join(uwtools_file_base, pathlib.Path("fixtures/simple2.nml"))

    with tempfile.TemporaryDirectory(dir=".") as tmp_dir:
        out_file = f"{tmp_dir}/test_config_from_nml.nml"
        args = ["-i", input_file, "-o", out_file, "-c", config_file]

        config.create_config_obj(args)

        expected = config.F90Config(input_file)
        config_file_obj = config.F90Config(config_file)
        expected.update_values(config_file_obj)
        expected_file = f"{tmp_dir}/expected_nml.nml"
        expected.dump_file(expected_file)

        assert compare_files(expected_file, out_file)


@pytest.mark.skip()
def test_set_config_ini_config_file():
    """Test that aproviding INI base input file and a config file will
    create and update INI config file"""

    input_file = os.path.join(uwtools_file_base, pathlib.Path("fixtures/simple.ini"))
    config_file = os.path.join(uwtools_file_base, pathlib.Path("fixtures/simple2.ini"))

    with tempfile.TemporaryDirectory(dir=".") as tmp_dir:
        out_file = f"{tmp_dir}/test_config_from_ini.ini"
        args = ["-i", input_file, "-o", out_file, "-c", config_file]

        config.create_config_obj(args)

        expected = config.INIConfig(input_file)
        config_file_obj = config.INIConfig(config_file)
        expected.update_values(config_file_obj)
        expected_file = f"{tmp_dir}/expected_ini.ini"
        expected.dump_file(expected_file)

        assert compare_files(expected_file, out_file)


@pytest.mark.skip()
def test_set_config_ini_bash_config_file():
    """Test that aproviding INI base input file and a config file will
    create and update INI config file"""

    input_file = os.path.join(uwtools_file_base, pathlib.Path("fixtures/simple.ini"))
    config_file = os.path.join(uwtools_file_base, pathlib.Path("fixtures/fruit_config.sh"))

    with tempfile.TemporaryDirectory(dir=".") as tmp_dir:
        out_file = f"{tmp_dir}/test_config_from_ini.ini"
        args = ["-i", input_file, "-o", out_file, "-c", config_file]

        config.create_config_obj(args)

        expected = config.INIConfig(input_file)
        config_file_obj = config.INIConfig(config_file)
        expected.update_values(config_file_obj)
        expected_file = f"{tmp_dir}/expected_ini.ini"
        expected.dump_file(expected_file)

        assert compare_files(expected_file, out_file)


@pytest.mark.skip()
def test_incompatible_file_type():
    """Test that providing an incompatible file type for input base file will
    return print statement"""

    input_file = os.path.join(uwtools_file_base, pathlib.Path("fixtures/model_configure.sample"))
    args = ["-i", input_file]

    with pytest.raises(ValueError):
        config.create_config_obj(args)


@pytest.mark.skip()
def test_set_config_field_table():
    """Test reading a YAML config object and generating a field file table."""
    input_file = os.path.join(uwtools_file_base, pathlib.Path("fixtures", "FV3_GFS_v16.yaml"))
    expected_file = os.path.join(
        uwtools_file_base, pathlib.Path("fixtures", "field_table.FV3_GFS_v16")
    )

    with tempfile.TemporaryDirectory(dir=".") as tmp_dir:
        out_file = f"{tmp_dir}/field_table_from_yaml.FV3_GFS"
        args = ["-i", input_file, "-o", out_file, "--output_file_type", "FieldTable"]

        config.create_config_obj(args)

        with open(expected_file, "r", encoding="utf-8") as f1, open(
            out_file, "r", encoding="utf-8"
        ) as f2:
            reflist = [line.rstrip("\n").strip().replace("'", "") for line in f1]
            outlist = [line.rstrip("\n").strip().replace("'", "") for line in f2]
            lines = zip(outlist, reflist)
            for line1, line2 in lines:
                assert line1 in line2


@pytest.mark.skip()
def test_set_config_dry_run():
    """Test that providing a YAML base file with a dry run flag
    will print an YAML config file"""

    input_file = os.path.join(uwtools_file_base, pathlib.Path("fixtures/fruit_config.yaml"))

    args = ["-i", input_file, "-d"]

    expected = config.YAMLConfig(input_file)
    expected.dereference_all()
    expected_content = str(expected)

    outstring = io.StringIO()
    with redirect_stdout(outstring):
        config.create_config_obj(args)
    result = outstring.getvalue()

    assert result.rstrip("\n") == expected_content.rstrip("\n")


@pytest.mark.skip()
def test_show_format():
    """Test providing required configuration format for a given input and target."""
    input_file = os.path.join(uwtools_file_base, pathlib.Path("fixtures", "FV3_GFS_v16.yaml"))
    outcome = """Help on method dump_file in module uwtools.config:

dump_file(output_path) method of uwtools.config.FieldTableConfig instance
    Write the formatted output to a text file. 
    FMS field and tracer managers must be registered in an ASCII table called 'field_table'
    This table lists field type, target model and methods the querying model will ask for.
    
    See UFS documentation for more information:
    https://ufs-weather-model.readthedocs.io/en/ufs-v1.0.0/InputsOutputs.html#field-table-file
    
    The example format for generating a field file is::
    
    sphum:
      longname: specific humidity
      units: kg/kg
      profile_type: 
        name: fixed
        surface_value: 1.e30

None
"""

    with tempfile.TemporaryDirectory(dir=".") as tmp_dir:
        out_file = f"{tmp_dir}/field_table_from_yaml.FV3_GFS"
        args = [
            "-i",
            input_file,
            "-o",
            out_file,
            "--show_format",
            "--output_file_type",
            "FieldTable",
        ]

        # Capture stdout for the required configuration settings
        outstring = io.StringIO()
        with redirect_stdout(outstring):
            config.create_config_obj(args)
        result = outstring.getvalue()

        assert result == outcome


@pytest.mark.skip()
def test_values_needed_yaml():
    """Test that the values_needed flag logs keys completed, keys containing
    unfilled jinja2 templates, and keys set to empty"""

    input_file = os.path.join(uwtools_file_base, pathlib.Path("fixtures/srw_example.yaml"))
    args = ["-i", input_file, "--values_needed"]

    # Capture stdout for values_needed output
    outstring = io.StringIO()
    with redirect_stdout(outstring):
        config.create_config_obj(args)
    result = outstring.getvalue()
    outcome = """Keys that are complete:
    FV3GFS
    FV3GFS.nomads
    FV3GFS.nomads.protocol
    FV3GFS.nomads.file_names
    FV3GFS.nomads.file_names.grib2
    FV3GFS.nomads.file_names.testfalse
    FV3GFS.nomads.file_names.testzero

Keys that have unfilled jinja2 templates:
    FV3GFS.nomads.url: https://nomads.ncep.noaa.gov/pub/data/nccf/com/gfs/prod/gfs.{{ yyyymmdd }}/{{ hh }}/atmos
    FV3GFS.nomads.file_names.grib2.anl: ['gfs.t{{ hh }}z.atmanl.nemsio','gfs.t{{ hh }}z.sfcanl.nemsio']
    FV3GFS.nomads.file_names.grib2.fcst: ['gfs.t{{ hh }}z.pgrb2.0p25.f{{ fcst_hr03d }}']

Keys that are set to empty:
    FV3GFS.nomads.file_names.nemsio
    FV3GFS.nomads.testempty
"""
    assert result == outcome


@pytest.mark.skip()
def test_values_needed_ini():
    """Test that the values_needed flag logs keys completed, keys containing
    unfilled jinja2 templates, and keys set to empty"""

    input_file = os.path.join(uwtools_file_base, pathlib.Path("fixtures/simple3.ini"))
    args = ["-i", input_file, "--values_needed"]

    # Capture stdout for values_needed output
    outstring = io.StringIO()
    with redirect_stdout(outstring):
        config.create_config_obj(args)
    result = outstring.getvalue()

    outcome = """Keys that are complete:
    salad
    salad.base
    salad.fruit
    salad.vegetable
    salad.dressing
    dessert
    dessert.type
    dessert.side
    dessert.servings

Keys that have unfilled jinja2 templates:
    salad.how_many: {{amount}}
    dessert.flavor: {{flavor}}

Keys that are set to empty:
    salad.toppings
    salad.meat
"""
    assert result == outcome


def test_values_needed_f90nml(capsys):
    """
    Test that the values_needed flag logs keys completed, keys containing
    unfilled jinja2 templates, and keys set to empty.
    """
    config.create_config_obj(
        parse_config_args(["-i", fixture_path("simple3.nml"), "--values_needed"])
    )
    actual = capsys.readouterr().out
    expected = """
Keys that are complete:
    salad
    salad.base
    salad.fruit
    salad.vegetable
    salad.how_many
    salad.extras
    salad.dessert

Keys that have unfilled jinja2 templates:
    salad.dressing: {{ dressing }}

Keys that are set to empty:
    salad.toppings
    salad.appetizer
""".lstrip()
    assert actual == expected


def test_cfg_to_yaml_conversion(tmp_path):
    """Test that a .cfg file can be used to create a YAML object."""
    infile = fixture_path("srw_example_yaml.cfg")
    outfile = str(tmp_path / "test_ouput.yaml")
    config.create_config_obj(
        parse_config_args(["-i", infile, "-o", outfile, "--input_file_type", "YAML"])
    )
    expected = config.YAMLConfig(infile)
    expected.dereference_all()
    expected_file = tmp_path / "test.yaml"
    expected.dump_file(expected_file)
    assert compare_files(expected_file, outfile)
    with open(outfile, "r", encoding="utf-8") as f:
        assert f.read()[-1] == "\n"


def test_output_file_conversion(tmp_path):
    """
    Test that --output_input_type converts config object to desired object type.
    """
    infile = fixture_path("simple.nml")
    outfile = str(tmp_path / "test_ouput.cfg")
    config.create_config_obj(
        parse_config_args(["-i", infile, "-o", outfile, "--output_file_type", "F90"])
    )
    expected = config.F90Config(infile)
    expected_file = tmp_path / "expected_nml.nml"
    expected.dump_file(expected_file)
    assert compare_files(expected_file, outfile)
    with open(outfile, "r", encoding="utf-8") as f:
        assert f.read()[-1] == "\n"


def test_config_file_conversion(tmp_path):
    """
    Test that --config_input_type converts config object to desired object type.
    """
    infile = fixture_path("simple2.nml")
    cfgfile = fixture_path("simple2.ini")
    outfile = str(tmp_path / "test_config_conversion.nml")
    config.create_config_obj(
        parse_config_args(["-i", infile, "-c", cfgfile, "-o", outfile, "--config_file_type", "F90"])
    )
    expected = config.F90Config(infile)
    config_obj = config.F90Config(cfgfile)
    expected.update_values(config_obj)
    expected_file = tmp_path / "expected_nml.nml"
    expected.dump_file(expected_file)
    assert compare_files(expected_file, outfile)
    with open(outfile, "r", encoding="utf-8") as f:
        assert f.read()[-1] == "\n"


def test_bad_conversion_cfg_to_pdf():
    with pytest.raises(SystemExit):
        config.create_config_obj(
            parse_config_args(["-i", fixture_path("simple2_nml.cfg"), "--input_file_type", ".pdf"])
        )


def test_bad_conversion_nml_to_yaml():
    with pytest.raises(ValueError):
        config.create_config_obj(
            parse_config_args(
                [
                    "-i",
                    fixture_path("simple2.nml"),
                    "-c",
                    fixture_path("srw_example.yaml"),
                    "--config_file_type",
                    "YAML",
                ]
            )
        )


def test_bad_conversion_yaml_to_nml(tmp_path):
    with pytest.raises(ValueError):
        config.create_config_obj(
            parse_config_args(
                [
                    "-i",
                    fixture_path("srw_example.yaml"),
                    "-o",
                    str(tmp_path / "test_outfile_conversion.yaml"),
                    "--output_file_type",
                    "F90",
                ]
            )
        )


def test_compare_nml(capsys):
    """Tests whether comparing two namelists works."""

    nml1 = fixture_path("fruit_config.nml")
    nml2 = fixture_path("fruit_config_mult_sect.nml")
    config.create_config_obj(parse_config_args(["-i", nml1, "-c", nml2, "--compare"]))
    actual = capsys.readouterr().out.split("\n")

    # Make sure the tool output contains all the expected lines:

    expected = f"""
- {nml1}
+ {nml2}
--------------------------------------------------------------------------------
config:       vegetable:  - eggplant + peas
setting:         topping:  - None + crouton
setting:            size:  - None + large
setting:            meat:  - None + chicken
""".strip()

    for line in expected.split("\n"):
        assert line_in_lines(line, actual)

    # Make sure it doesn't include any additional significant diffs
    # A very rough estimate is that there is a word/colon set followed
    # by a -/+ set
    # This regex is meant to match the lines in the expected string
    # above that give us the section, key value diffs like this:
    #   config:       vegetable:  - eggplant + peas

    pattern = re.compile(r"\w:\s+\w+:\s+-\s+\w+\s+\+\s+\w+")
    for line in actual:
        if re.search(pattern, line):
            assert line in expected
