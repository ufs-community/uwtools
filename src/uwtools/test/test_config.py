# pylint: disable=duplicate-code,missing-function-docstring,redefined-outer-name

"""
Set of test for loading YAML files using the function call load_yaml
"""

import builtins
import datetime
import filecmp
import itertools
import json
import logging
import os
import pathlib
import re
import sys
import tempfile
from argparse import ArgumentTypeError
from pathlib import Path
from unittest.mock import patch

import pytest
from pytest import fixture, raises

from uwtools import config, exceptions, logger
from uwtools.cli.set_config import parse_args as parse_config_args
from uwtools.test.support import compare_files, fixture_path, line_in_lines, msg_in_caplog_records
from uwtools.utils import cli_helpers

# Helpers


@fixture
def salad_base():
    return {
        "salad": {
            "base": "kale",
            "fruit": "banana",
            "vegetable": "tomato",
            "how_many": "12",
            "dressing": "balsamic",
        }
    }


def help_cfgclass(ext):
    return getattr(
        config, "%sConfig" % {".nml": "F90", ".ini": "INI", ".sh": "INI", ".yaml": "YAML"}[ext]
    )


def help_set_config_simple(infn, tmpdir):
    infile = fixture_path(infn)
    ext = Path(infile).suffix
    outfile = str(tmpdir / f"outfile{ext}")
    config.create_config_obj(parse_config_args(["-i", infile, "-o", outfile]))
    cfgobj = help_cfgclass(ext)(infile)
    reference = tmpdir / f"reference{ext}"
    cfgobj.dump_file(reference)
    assert compare_files(reference, outfile)


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


# Tests

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


def test_bad_conversion_cfg_to_pdf():
    with raises(SystemExit):
        config.create_config_obj(
            parse_config_args(["-i", fixture_path("simple2_nml.cfg"), "--input_file_type", ".pdf"])
        )


def test_bad_conversion_nml_to_yaml():
    with raises(ValueError):
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
    with raises(ValueError):
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


def test_cfg_to_yaml_conversion(tmp_path):
    """
    Test that a .cfg file can be used to create a YAML object.
    """
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


@pytest.mark.parametrize("fmt", ["F90", "INI", "YAML"])
def test_compare_config(fmt, salad_base, caplog):
    """Compare two config objects."""
    ext = ".%s" % ("nml" if fmt == "F90" else fmt).lower()
    cfgobj = help_cfgclass(ext)(fixture_path(f"simple{ext}"), log_name="test_compare_config")
    cfgobj.log.addHandler(logging.StreamHandler(sys.stdout))
    cfgobj.log.setLevel(logging.INFO)
    cfgobj.compare_config(cfgobj, salad_base)
    if fmt in ["F90", "YAML"]:
        assert msg_in_caplog_records("salad:        how_many:  - 12 + 12", caplog.records)
    else:
        assert not caplog.records  # #PM# BUT WHY NOT IN INI?
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
        assert msg_in_caplog_records(msg, caplog.records)


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
    expected_file = tmp_path / "expected.nml"
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
    Test that providing an incompatible file type for input base file will
    return print statement.
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
    expected = salad_base["salad"]
    assert cfgobj == expected
    cfgobj.dump_file(outfile)
    assert filecmp.cmp(infile, outfile)
    cfgobj.update({"dressing": ["ranch", "italian"]})
    expected["dressing"] = ["ranch", "italian"]
    assert cfgobj == expected


def test_ini_config_simple(salad_base, tmp_path):
    """
    Test that INI config load and dump work with a basic INI file. Everything in
    INI is treated as a string!
    """
    infile = fixture_path("simple.ini")
    outfile = tmp_path / "outfile.ini"
    cfgobj = config.INIConfig(infile)
    expected = salad_base
    assert cfgobj == expected
    cfgobj.dump_file(outfile)
    assert filecmp.cmp(infile, outfile)
    cfgobj.update({"dressing": ["ranch", "italian"]})
    expected["dressing"] = ["ranch", "italian"]
    assert cfgobj == expected


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
    expected_file = tmp_path / "expected.nml"
    expected.dump_file(expected_file)
    assert compare_files(expected_file, outfile)
    with open(outfile, "r", encoding="utf-8") as f:
        assert f.read()[-1] == "\n"


def test_path_if_file_exists(tmp_path):
    """
    Test that function raises an exception when the specified file does not
    exist, and raises no exception when the file exists.
    """

    badfile = tmp_path / "no-such-file"
    with raises(ArgumentTypeError):
        cli_helpers.path_if_file_exists(badfile)

    goodfile = tmp_path / "exists"
    with open(goodfile, "w", encoding="utf-8"):
        pass
    assert cli_helpers.path_if_file_exists(goodfile)


def test_set_config_dry_run(capsys):
    """
    Test that providing a YAML base file with a dry run flag will print an YAML
    config file.
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
        parse_config_args(["-i", infile, "-o", outfile, "--output_file_type", "FieldTable"])
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
    Test that providing a namelist base input file and a config file will create
    and update namelist config file.
    """
    help_set_config_fmt2fmt("simple.nml", "simple2.nml", tmp_path)


def test_set_config_fmt2fmt_ini2bash(tmp_path):
    """
    Test that providing an INI base input file and a Bash config file will
    create and update INI config file.
    """
    help_set_config_fmt2fmt("simple.ini", "fruit_config.sh", tmp_path)


def test_set_config_fmt2fmt_ini2ini(tmp_path):
    """
    Test that providing an INI base input file and an INI config file will
    create and update INI config file.
    """
    help_set_config_fmt2fmt("simple.ini", "simple2.ini", tmp_path)


def test_set_config_fmt2fmt_yaml2yaml(tmp_path):
    """
    Test that providing a YAML base input file and a YAML config file will
    create and update YAML config file.
    """
    help_set_config_fmt2fmt("fruit_config.yaml", "fruit_config_similar.yaml", tmp_path)


def test_set_config_simple_bash(tmp_path):
    """
    Test that providing a bash file with necessary settings will create an INI
    config file.
    """
    help_set_config_simple("simple.sh", tmp_path)


def test_set_config_simple_namelist(tmp_path):
    """
    Test that providing a namelist file with necessary settings will create a
    namelist config file.
    """
    help_set_config_simple("simple.nml", tmp_path)


def test_set_config_simple_ini(tmp_path):
    """
    Test that providing an INI file with necessary settings will create an INI
    config file.
    """
    help_set_config_simple("simple.ini", tmp_path)


def test_set_config_simple_yaml(tmp_path):
    """
    Test that providing a YAML base file with necessary settings will create a
    YAML config file.
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
            "--show_format",
            "--output_file_type",
            "YAML",
        ]
    )
    with patch.object(builtins, "help") as mock_help:
        # Since file types match, help() is not called:
        config.create_config_obj(args)
        mock_help.assert_not_called()
        # But help() is called when the input is YAML and the output FieldTable:
        args.output_file_type = "FieldTable"
        config.create_config_obj(args)
        mock_help.assert_called_once()


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
    Test that the values_needed flag logs keys completed, keys containing
    unfilled jinja2 templates, and keys set to empty.
    """
    config.create_config_obj(
        parse_config_args(["-i", fixture_path("simple3.ini"), "--values_needed"])
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


def test_values_needed_yaml(capsys):
    """
    Test that the values_needed flag logs keys completed, keys containing
    unfilled jinja2 templates, and keys set to empty.
    """
    config.create_config_obj(
        parse_config_args(["-i", fixture_path("srw_example.yaml"), "--values_needed"])
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
    # #PM# WHAT IS THE RATIONALE HERE?
    assert "value is included in quotes" in str(e.value)


def test_yaml_constructor_error_unregistered_constructor(tmp_path):
    # Test that unregistered constructor raises UWConfigError.

    tmpfile = tmp_path / "test.yaml"
    with tmpfile.open("w", encoding="utf-8") as f:
        f.write(
            """
foo: !not_a_constructor bar
"""
        )
    with raises(exceptions.UWConfigError) as e:
        config.YAMLConfig(tmpfile)
    assert "constructor: '!not_a_constructor'" in str(e.value)
    assert "Define the constructor before proceeding" in str(e.value)
