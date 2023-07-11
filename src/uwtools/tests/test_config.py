# pylint: disable=duplicate-code,missing-function-docstring,redefined-outer-name
"""
Tests for uwtools.config module.
"""

import builtins
import datetime
import filecmp
import itertools
import logging
import os
import re
import sys
from argparse import ArgumentTypeError
from collections import OrderedDict
from pathlib import Path
from typing import Any, List
from unittest.mock import patch

import pytest
import yaml
from pytest import fixture, raises

from uwtools import config, exceptions, logger
from uwtools.cli.set_config import parse_args as parse_config_args
from uwtools.exceptions import UWConfigError
from uwtools.tests.support import compare_files, fixture_path, line_in_lines, msg_in_caplog
from uwtools.utils import cli_helpers

# Helper functions


def help_cfgclass(ext):
    return getattr(
        config, "%sConfig" % {".nml": "F90", ".ini": "INI", ".sh": "INI", ".yaml": "YAML"}[ext]
    )


def help_set_config_fmt2fmt(infn, cfgfn, tmpdir):
    infile = fixture_path(infn)
    cfgfile = fixture_path(cfgfn)
    ext = Path(infile).suffix
    outfile = str(tmpdir / f"outfile{ext}")
    config.create_config_obj(parse_config_args(["-i", infile, "-o", outfile, "-c", cfgfile]))
    cfgclass = getattr(config, "%sConfig" % {".nml": "F90", ".ini": "INI", ".yaml": "YAML"}[ext])
    cfgobj = cfgclass(infile)
    cfgobj.update_values(cfgclass(cfgfile))
    reference = tmpdir / "expected"
    cfgobj.dump_file(reference)
    assert compare_files(reference, outfile)


def help_set_config_simple(infn, tmpdir):
    infile = fixture_path(infn)
    ext = Path(infile).suffix
    outfile = str(tmpdir / f"outfile{ext}")
    config.create_config_obj(parse_config_args(["-i", infile, "-o", outfile]))
    cfgobj = help_cfgclass(ext)(infile)
    reference = tmpdir / f"reference{ext}"
    cfgobj.dump_file(reference)
    assert compare_files(reference, outfile)


# Test functions


def test_bad_conversion_cfg_to_pdf(capsys):
    with raises(SystemExit):
        config.create_config_obj(
            parse_config_args(["-i", fixture_path("simple2_nml.cfg"), "--input-file-type", ".pdf"])
        )
    assert "invalid choice: '.pdf'" in capsys.readouterr().err


def test_bad_conversion_nml_to_yaml():
    with raises(ValueError):
        config.create_config_obj(
            parse_config_args(
                [
                    "-i",
                    fixture_path("simple2.nml"),
                    "-c",
                    fixture_path("srw_example.yaml"),
                    "--config-file-type",
                    "YAML",
                ]
            )
        )


def test_bad_conversion_yaml_to_nml(tmp_path):
    with raises(ValueError):
        config.create_config_obj(
            parse_config_args(
                [
                    "-i",
                    fixture_path("srw_example.yaml"),
                    "-o",
                    str(tmp_path / "test_outfile_conversion.yaml"),
                    "--output-file-type",
                    "F90",
                ]
            )
        )


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


@pytest.mark.parametrize("fmt", ["F90", "INI", "YAML"])
def test_compare_config(fmt, salad_base, caplog):
    """
    Compare two config objects.
    """
    ext = ".%s" % ("nml" if fmt == "F90" else fmt).lower()
    cfgobj = help_cfgclass(ext)(fixture_path(f"simple{ext}"))
    cfgobj.log.addHandler(logging.StreamHandler(sys.stdout))
    cfgobj.log.setLevel(logging.INFO)
    if fmt == "INI":
        salad_base["salad"]["how_many"] = "12"  # str "12" (not int 12) for INI
    cfgobj.compare_config(cfgobj, salad_base)
    # Expect no differences:
    assert not caplog.records
    caplog.clear()
    # Create differences in base dict:
    salad_base["salad"]["dressing"] = "italian"
    salad_base["salad"]["size"] = "large"
    del salad_base["salad"]["how_many"]
    cfgobj.compare_config(cfgobj, salad_base)
    # Expect to see the following differences logged:
    for msg in [
        "salad:        dressing:  - italian + balsamic",
        "salad:            size:  - large + None",
        "salad:        how_many:  - None + 12",
    ]:
        assert msg_in_caplog(msg, caplog.records)


def test_compare_nml(capsys):
    """
    Tests whether comparing two namelists works.
    """
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


def test_config_field_table(tmp_path):
    """
    Test reading a YAML config object and generating a field table file.
    """
    cfgfile = fixture_path("FV3_GFS_v16.yaml")
    outfile = tmp_path / "field_table_from_yaml.FV3_GFS"
    reference = fixture_path("field_table.FV3_GFS_v16")
    config.FieldTableConfig(cfgfile).dump_file(outfile)
    with open(reference, "r", encoding="utf-8") as f1:
        reflines = [line.strip().replace("'", "") for line in f1]
    with open(outfile, "r", encoding="utf-8") as f2:
        outlines = [line.strip().replace("'", "") for line in f2]
    for line1, line2 in zip(outlines, reflines):
        assert line1 == line2


def test_config_file_conversion(tmp_path):
    """
    Test that --config-input-type converts config object to desired object type.
    """
    infile = fixture_path("simple2.nml")
    cfgfile = fixture_path("simple2.ini")
    outfile = str(tmp_path / "test_config_conversion.nml")
    config.create_config_obj(
        parse_config_args(["-i", infile, "-c", cfgfile, "-o", outfile, "--config-file-type", "F90"])
    )
    expected = config.F90Config(infile)
    config_obj = config.F90Config(cfgfile)
    expected.update_values(config_obj)
    expected_file = tmp_path / "expected.nml"
    expected.dump_file(expected_file)
    assert compare_files(expected_file, outfile)
    with open(outfile, "r", encoding="utf-8") as f:
        assert f.read()[-1] == "\n"


def test_conversion_cfg_to_yaml(tmp_path):
    """
    Test that a .cfg file can be used to create a YAML object.
    """
    infile = fixture_path("srw_example_yaml.cfg")
    outfile = str(tmp_path / "test_ouput.yaml")
    config.create_config_obj(
        parse_config_args(["-i", infile, "-o", outfile, "--input-file-type", "YAML"])
    )
    expected = config.YAMLConfig(infile)
    expected.dereference_all()
    expected_file = tmp_path / "test.yaml"
    expected.dump_file(expected_file)
    assert compare_files(expected_file, outfile)
    with open(outfile, "r", encoding="utf-8") as f:
        assert f.read()[-1] == "\n"


def test_dereference():
    """
    Test that the Jinja2 fields are filled in as expected.
    """
    with patch.dict(os.environ, {"UFSEXEC": "/my/path/"}):
        cfg = config.YAMLConfig(fixture_path("gfs.yaml"))
        cfg.dereference_all()

        # Check that existing dicts remain:
        assert isinstance(cfg["fcst"], dict)
        assert isinstance(cfg["grid_stats"], dict)

        # Check references to other items at same level, and order doesn't
        # matter:
        assert cfg["testupdate"] == "testpassed"

        # Check references to other section items:
        assert cfg["grid_stats"]["ref_fcst"] == 64

        # Check environment values are included:
        assert cfg["executable"] == "/my/path/"

        # Check that env variables that are not defined do not change:
        assert cfg["undefined_env"] == "{{ NOPE }}"

        # Check undefined are left as-is:
        assert cfg["datapath"] == "{{ [experiment_dir, current_cycle] | path_join }}"

        # Check math:
        assert cfg["grid_stats"]["total_points"] == 640000
        assert cfg["grid_stats"]["total_ens_points"] == 19200000

        # Check that statements expand:
        assert cfg["fcst"]["output_hours"] == "0 3 6 9 "

        # Check that order isn't a problem:
        assert cfg["grid_stats"]["points_per_level"] == 10000


def test_dereference_exceptions(caplog):
    """
    Test that dereference handles some standard mistakes.
    """
    log = logger.Logger(name="test_dereference_exceptions", level="DEBUG")
    cfg = config.YAMLConfig(log_name=log.name)
    cfg.update({"undefined_filter": "{{ 34 | im_not_a_filter }}"})
    with raises(exceptions.UWConfigError) as e:
        cfg.dereference()
    assert "filter: 'im_not_a_filter'" in str(e.value)
    cfg.pop("undefined_filter", None)
    cfg.update(
        {
            "divide": "{{ num // nada }}",  # ZeroDivisionError
            "foo": "bar",
            "list_a": [1, 2, 4],
            "nada": 0,
            "num": 2,
            "soap": "{{ foo }}",
            "type_prob": '{{ list_a / "a" }}',  # TypeError
        }
    )
    caplog.clear()
    cfg.dereference()
    raised = [rec.msg for rec in caplog.records if "raised" in rec.msg]
    assert "ZeroDivisionError" in raised[0]
    assert "TypeError" in raised[1]


@pytest.mark.parametrize(
    "fn,depth", [("FV3_GFS_v16.yaml", 3), ("simple.nml", 2), ("simple2.ini", 2)]
)
def test_dictionary_depth(fn, depth):
    """
    Test that the proper dictionary depth is returned for each file type.
    """
    infile = fixture_path(fn)
    ext = Path(infile).suffix
    cfgobj = help_cfgclass(ext)(infile)
    assert cfgobj.dictionary_depth(cfgobj.data) == depth


def test_f90nml_config_simple(salad_base, tmp_path):
    """
    Test that namelist load, update, and dump work with a basic namelist file.
    """
    infile = fixture_path("simple.nml")
    outfile = tmp_path / "outfile.nml"
    cfgobj = config.F90Config(infile)
    expected = salad_base
    expected["salad"]["how_many"] = 12  # must be in for nml
    assert cfgobj == expected
    cfgobj.dump_file(outfile)
    assert filecmp.cmp(infile, outfile)
    cfgobj.update({"dressing": ["ranch", "italian"]})
    expected["dressing"] = ["ranch", "italian"]
    assert cfgobj == expected


def test_incompatible_file_type():
    """
    Test that providing an incompatible file type for input base file will return print statement.
    """
    with raises(ValueError):
        config.create_config_obj(parse_config_args(["-i", fixture_path("model_configure.sample")]))


def test_ini_config_bash(salad_base, tmp_path):
    """
    Test that INI config load and dump work with a basic bash file.
    """
    infile = fixture_path("simple.sh")
    outfile = tmp_path / "outfile.sh"
    cfgobj = config.INIConfig(infile, space_around_delimiters=False)
    expected = {**salad_base["salad"], "how_many": "12"}  # str "12" (not int 12) for INI
    assert cfgobj == expected
    cfgobj.dump_file(outfile)
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
    cfgobj = config.INIConfig(infile)
    expected = salad_base
    expected["salad"]["how_many"] = "12"  # str "12" (not int 12) for INI
    assert cfgobj == expected
    cfgobj.dump_file(outfile)
    assert filecmp.cmp(infile, outfile)
    cfgobj.update({"dressing": ["ranch", "italian"]})
    expected["dressing"] = ["ranch", "italian"]
    assert cfgobj == expected


def test_output_file_conversion(tmp_path):
    """
    Test that --output-input-type converts config object to desired object type.
    """
    infile = fixture_path("simple.nml")
    outfile = str(tmp_path / "test_ouput.cfg")
    config.create_config_obj(
        parse_config_args(["-i", infile, "-o", outfile, "--output-file-type", "F90"])
    )
    expected = config.F90Config(infile)
    expected_file = tmp_path / "expected.nml"
    expected.dump_file(expected_file)
    assert compare_files(expected_file, outfile)
    with open(outfile, "r", encoding="utf-8") as f:
        assert f.read()[-1] == "\n"


def test_parse_include():
    """
    Test that non-YAML handles !INCLUDE Tags properly.
    """
    cfgobj = config.F90Config(fixture_path("include_files.nml"))
    assert cfgobj["config"]["fruit"] == "papaya"
    assert cfgobj["config"]["how_many"] == 17
    assert cfgobj["config"]["meat"] == "beef"
    assert len(cfgobj["config"]) == 5


def test_parse_include_ini():
    """
    Test that non-YAML handles !INCLUDE Tags properly for INI with no sections.
    """
    cfgobj = config.INIConfig(fixture_path("include_files.sh"), space_around_delimiters=False)
    assert cfgobj.get("fruit") == "papaya"
    assert cfgobj.get("how_many") == "17"
    assert cfgobj.get("meat") == "beef"
    assert len(cfgobj) == 5


def test_parse_include_mult_sect():
    """
    Test that non-YAML handles !INCLUDE tags with files that have multiple sections in separate
    file.
    """
    cfgobj = config.F90Config(fixture_path("include_files_with_sect.nml"))
    assert cfgobj["config"]["fruit"] == "papaya"
    assert cfgobj["config"]["how_many"] == 17
    assert cfgobj["config"]["meat"] == "beef"
    assert cfgobj["config"]["dressing"] == "ranch"
    assert cfgobj["setting"]["size"] == "large"
    assert len(cfgobj["config"]) == 5
    assert len(cfgobj["setting"]) == 3


def test_path_if_file_exists(tmp_path):
    """
    Test that function raises an exception when the specified file does not exist, and raises no
    exception when the file exists.
    """

    badfile = tmp_path / "no-such-file"
    with raises(ArgumentTypeError):
        cli_helpers.path_if_file_exists(badfile)

    goodfile = tmp_path / "exists"
    goodfile.touch()
    assert cli_helpers.path_if_file_exists(goodfile)


def test_set_config_dry_run(capsys):
    """
    Test that providing a YAML base file with a dry run flag will print an YAML config file.
    """
    infile = fixture_path("fruit_config.yaml")
    yaml_config = config.YAMLConfig(infile)
    yaml_config.dereference_all()
    config.create_config_obj(parse_config_args(["-i", infile, "-d"]))
    actual = capsys.readouterr().out.strip()
    expected = str(yaml_config).strip()
    assert actual == expected


def test_set_config_field_table(tmp_path):
    """
    Test reading a YAML config object and generating a field file table.
    """
    infile = fixture_path("FV3_GFS_v16.yaml")
    outfile = str(tmp_path / "field_table_from_yaml.FV3_GFS")
    config.create_config_obj(
        parse_config_args(["-i", infile, "-o", outfile, "--output-file-type", "FieldTable"])
    )
    with open(fixture_path("field_table.FV3_GFS_v16"), "r", encoding="utf-8") as f1:
        with open(outfile, "r", encoding="utf-8") as f2:
            reflist = [line.rstrip("\n").strip().replace("'", "") for line in f1]
            outlist = [line.rstrip("\n").strip().replace("'", "") for line in f2]
            lines = zip(outlist, reflist)
            for line1, line2 in lines:
                assert line1 in line2


def test_set_config_fmt2fmt_nml2nml(tmp_path):
    """
    Test that providing a namelist base input file and a config file will create and update namelist
    config file.
    """
    help_set_config_fmt2fmt("simple.nml", "simple2.nml", tmp_path)


def test_set_config_fmt2fmt_ini2bash(tmp_path):
    """
    Test that providing an INI base input file and a Bash config file will create and update INI
    config file.
    """
    help_set_config_fmt2fmt("simple.ini", "fruit_config.sh", tmp_path)


def test_set_config_fmt2fmt_ini2ini(tmp_path):
    """
    Test that providing an INI base input file and an INI config file will create and update INI
    config file.
    """
    help_set_config_fmt2fmt("simple.ini", "simple2.ini", tmp_path)


def test_set_config_fmt2fmt_yaml2yaml(tmp_path):
    """
    Test that providing a YAML base input file and a YAML config file will create and update YAML
    config file.
    """
    help_set_config_fmt2fmt("fruit_config.yaml", "fruit_config_similar.yaml", tmp_path)


def test_set_config_simple_bash(tmp_path):
    """
    Test that providing a bash file with necessary settings will create an INI config file.
    """
    help_set_config_simple("simple.sh", tmp_path)


def test_set_config_simple_namelist(tmp_path):
    """
    Test that providing a namelist file with necessary settings will create a namelist config file.
    """
    help_set_config_simple("simple.nml", tmp_path)


def test_set_config_simple_ini(tmp_path):
    """
    Test that providing an INI file with necessary settings will create an INI config file.
    """
    help_set_config_simple("simple.ini", tmp_path)


def test_set_config_simple_yaml(tmp_path):
    """
    Test that providing a YAML base file with necessary settings will create a YAML config file.
    """
    help_set_config_simple("simple2.yaml", tmp_path)


def test_show_format():
    """
    Test providing required configuration format for a given input and target.
    """
    # Initially, input and output file types are both YAML:
    args = parse_config_args(
        [
            "-i",
            fixture_path("FV3_GFS_v16.yaml"),
            "-o",
            "/dev/null",
            "--show-format",
            "--output-file-type",
            "YAML",
        ]
    )
    with patch.object(builtins, "help") as help_:
        # Since file types match, help() is not called:
        config.create_config_obj(args)
        help_.assert_not_called()
        # But help() is called when the input is YAML and the output FieldTable:
        args.output_file_type = "FieldTable"
        config.create_config_obj(args)
        help_.assert_called_once()


def test_transform_config(tmp_path):
    """
    Test that transforms config objects to objects of other config subclasses.
    """
    # Use itertools to construct all pairs of the config formats and iterate
    # through their corresponding classes. The transforms here ensure consistent
    # file subscripts and config calls.

    for fmt1, fmt2 in itertools.permutations(["INI", "YAML", "F90"], 2):
        ext1, ext2 = [".%s" % ("NML" if x == "F90" else x).lower() for x in (fmt1, fmt2)]
        outfile = tmp_path / f"test_{fmt1.lower()}to{fmt2.lower()}_dump{ext2}"
        reference = fixture_path(f"simple{ext2}")
        cfgin = help_cfgclass(ext1)(fixture_path(f"simple{ext1}"))
        cfgout = help_cfgclass(ext2)()
        cfgout.update(cfgin.data)
        cfgout.dump_file(outfile)
        with open(reference, "r", encoding="utf-8") as f1:
            reflines = [line.strip().replace("'", "") for line in f1]
        with open(outfile, "r", encoding="utf-8") as f2:
            outlines = [line.strip().replace("'", "") for line in f2]
        for line1, line2 in zip(reflines, outlines):
            assert line1 == line2


def test_values_needed_ini(capsys):
    """
    Test that the values_needed flag logs keys completed, keys containing unfilled jinja2 templates,
    and keys set to empty.
    """
    config.create_config_obj(
        parse_config_args(["-i", fixture_path("simple3.ini"), "--values-needed"])
    )
    actual = capsys.readouterr().out
    expected = """
Keys that are complete:
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
""".lstrip()
    assert actual == expected


def test_values_needed_f90nml(capsys):
    """
    Test that the values_needed flag logs keys completed, keys containing unfilled jinja2 templates,
    and keys set to empty.
    """
    config.create_config_obj(
        parse_config_args(["-i", fixture_path("simple3.nml"), "--values-needed"])
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


def test_values_needed_yaml(capsys):
    """
    Test that the values_needed flag logs keys completed, keys containing unfilled jinja2 templates,
    and keys set to empty.
    """
    config.create_config_obj(
        parse_config_args(["-i", fixture_path("srw_example.yaml"), "--values-needed"])
    )
    actual = capsys.readouterr().out
    expected = """
Keys that are complete:
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
""".lstrip()
    assert actual == expected


def test_yaml_config_composite_types():
    """
    Test that YAML load and dump work with a YAML file that has multiple data structures and levels.
    """
    cfgobj = config.YAMLConfig(fixture_path("result4.yaml"))

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
    Test that including files via the !INCLUDE constructor works as expected.
    """
    cfgobj = config.YAMLConfig(fixture_path("include_files.yaml"))

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
    cfgobj = config.YAMLConfig(infile)
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
    cfgobj.dump_file(outfile)
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
        config.YAMLConfig(tmpfile)
    assert "value is enclosed in quotes" in str(e.value)


def test_yaml_constructor_error_unregistered_constructor(tmp_path):
    # Test that unregistered constructor raises UWConfigError.

    tmpfile = tmp_path / "test.yaml"
    with tmpfile.open("w", encoding="utf-8") as f:
        f.write("foo: !not_a_constructor bar")
    with raises(exceptions.UWConfigError) as e:
        config.YAMLConfig(tmpfile)
    assert "constructor: '!not_a_constructor'" in str(e.value)
    assert "Define the constructor before proceeding" in str(e.value)


@fixture
def f90_cfgobj(tmp_path):
    # Use F90Config to exercise methods in Config abstract base class.
    path = tmp_path / "cfg.nml"
    with open(path, "w", encoding="utf-8") as f:
        f.write("&nl n = 88 /")
    return config.F90Config(config_path=path)


def test_Config___repr__(f90_cfgobj, capsys):
    print(f90_cfgobj)
    assert yaml.safe_load(capsys.readouterr().out)["nl"]["n"] == 88


def test_Config_dereference_unexpected_error(f90_cfgobj):
    exctype = FloatingPointError
    with patch.object(config.J2Template, "render_template", side_effect=exctype):
        with raises(exctype):
            f90_cfgobj.dereference(ref_dict={"n": "{{ n }}"})


def test_Config_from_ordereddict(f90_cfgobj):
    d: dict[Any, Any] = OrderedDict([("z", 26), ("a", OrderedDict([("alpha", 1)]))])
    d = f90_cfgobj.from_ordereddict(d)
    # Assert that every OrderedDict is now just a dict. The second assert is needed because
    # isinstance(OrderedDict(), dict) is True.
    for x in d, d["a"]:
        assert isinstance(x, dict)
        assert not isinstance(x, OrderedDict)


def test_Config_iterate_values(f90_cfgobj):
    empty_var: List[str] = []
    jinja2_var: List[str] = []
    set_var: List[str] = []
    d = {1: "", 2: None, 3: "{{ n }}", 4: {"a": 88}, 5: [{"b": 99}], 6: "string"}
    f90_cfgobj.iterate_values(
        config_dict=d, empty_var=empty_var, jinja2_var=jinja2_var, set_var=set_var, parent="p"
    )
    assert empty_var == ["    p1", "    p2"]
    assert jinja2_var == ["    p3: {{ n }}"]
    assert set_var == ["    p4", "    p4.a", "    p5", "    pb", "    p6"]


def test_Config_str_to_type(f90_cfgobj):
    for x in ["true", "yes", "yeah"]:
        assert f90_cfgobj.str_to_type(x) is True
    for x in ["false", "no", "nope"]:
        assert f90_cfgobj.str_to_type(x) is False
    assert f90_cfgobj.str_to_type("88") == 88
    assert f90_cfgobj.str_to_type("3.14") == 3.14
    assert f90_cfgobj.str_to_type("NA") == "NA"  # no conversion


def test_YAMLConfig__load_unexpected_error(tmp_path):
    cfgfile = tmp_path / "cfg.yaml"
    with open(cfgfile, "w", encoding="utf-8") as f:
        print("{n: 88}", file=f)
    with patch.object(config.yaml, "load") as load:
        msg = "Unexpected error"
        load.side_effect = yaml.constructor.ConstructorError(note=msg)
        with raises(UWConfigError) as e:
            config.YAMLConfig(config_path=cfgfile)
        assert msg in str(e.value)
