# pylint: disable=duplicate-code,missing-function-docstring,protected-access,redefined-outer-name
"""
Tests for uwtools.config module.
"""

import builtins
import datetime
import filecmp
import logging
import os
import re
from collections import OrderedDict
from io import StringIO
from pathlib import Path
from typing import Any, List
from unittest.mock import patch

import pytest
import yaml
from pytest import fixture, raises

from uwtools import exceptions
from uwtools.config import core
from uwtools.exceptions import UWConfigError
from uwtools.tests.support import compare_files, fixture_path, logged
from uwtools.utils.cli import path_if_it_exists

# Helper functions


def help_cfgclass(ext):
    return getattr(
        core,
        "%sConfig"
        % {
            ".ini": "INI",
            ".nml": "NML",
            ".sh": "INI",
            ".yaml": "YAML",
        }[ext],
    )


def help_set_config_fmt2fmt(infn, cfgfn, tmpdir):
    infile = fixture_path(infn)
    cfgfile = fixture_path(cfgfn)
    ext = Path(infile).suffix
    outfile = str(tmpdir / f"outfile{ext}")
    core.create_config_obj(input_base_file=infile, config_file=cfgfile, outfile=outfile)
    cfgclass = getattr(
        core,
        "%sConfig"
        % {
            ".ini": "INI",
            ".nml": "NML",
            ".yaml": "YAML",
        }[ext],
    )
    cfgobj = cfgclass(infile)
    cfgobj.update_values(cfgclass(cfgfile))
    reference = tmpdir / "expected"
    cfgobj.dump_file(reference)
    assert compare_files(reference, outfile)


def help_set_config_simple(infn, tmpdir):
    infile = fixture_path(infn)
    ext = Path(infile).suffix
    outfile = str(tmpdir / f"outfile{ext}")
    core.create_config_obj(input_base_file=infile, outfile=outfile)
    cfgobj = help_cfgclass(ext)(infile)
    reference = tmpdir / f"reference{ext}"
    cfgobj.dump_file(reference)
    assert compare_files(reference, outfile)


# Test functions


def test_bad_conversion_nml_to_yaml():
    with raises(ValueError):
        core.create_config_obj(
            input_base_file=fixture_path("simple2.nml"),
            config_file=fixture_path("srw_example.yaml"),
            config_file_type="YAML",
        )


def test_bad_conversion_yaml_to_nml(tmp_path):
    with raises(ValueError):
        core.create_config_obj(
            input_base_file=fixture_path("srw_example.yaml"),
            outfile=str(tmp_path / "test_outfile_conversion.yaml"),
            output_file_type="NML",
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


@pytest.mark.parametrize("fmt", ["INI", "NML", "YAML"])
def test_compare_config(caplog, fmt, salad_base):
    """
    Compare two config objects.
    """
    logging.getLogger().setLevel(logging.INFO)
    ext = ".%s" % ("nml" if fmt == "NML" else fmt).lower()
    cfgobj = help_cfgclass(ext)(fixture_path(f"simple{ext}"))
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
        assert logged(caplog, msg)


def test_compare_nml(caplog):
    """
    Tests whether comparing two namelists works.
    """
    logging.getLogger().setLevel(logging.INFO)
    nml1 = fixture_path("fruit_config.nml")
    nml2 = fixture_path("fruit_config_mult_sect.nml")
    core.create_config_obj(input_base_file=nml1, config_file=nml2, compare=True)
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
        assert logged(caplog, line)
    # Make sure it doesn't include any additional significant diffs
    # A very rough estimate is that there is a word/colon set followed
    # by a -/+ set
    # This regex is meant to match the lines in the expected string
    # above that give us the section, key value diffs like this:
    #   config:       vegetable:  - eggplant + peas
    pattern = re.compile(r"\w:\s+\w+:\s+-\s+\w+\s+\+\s+\w+")
    for line in [record.message for record in caplog.records]:
        if re.search(pattern, line):
            assert line in expected


def test_config_field_table(tmp_path):
    """
    Test reading a YAML config object and generating a field table file.
    """
    cfgfile = fixture_path("FV3_GFS_v16.yaml")
    outfile = tmp_path / "field_table_from_yaml.FV3_GFS"
    reference = fixture_path("field_table.FV3_GFS_v16")
    core.FieldTableConfig(cfgfile).dump_file(outfile)
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
    core.create_config_obj(
        input_base_file=infile, config_file=cfgfile, outfile=outfile, config_file_type="NML"
    )
    expected = core.NMLConfig(infile)
    config_obj = core.NMLConfig(cfgfile)
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
    core.create_config_obj(input_base_file=infile, outfile=outfile, input_file_type="YAML")
    expected = core.YAMLConfig(infile)
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
        cfg = core.YAMLConfig(fixture_path("gfs.yaml"))
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


def test_dereference_bad_filter(tmp_path):
    """
    Test that an unregistered filter is detected and treated as an error.
    """
    path = tmp_path / "cfg.yaml"
    with open(path, "w", encoding="utf-8") as f:
        print("undefined_filter: '{{ 34 | not_a_filter }}'", file=f)
    cfg = core.YAMLConfig(config_path=path)
    with raises(exceptions.UWConfigError) as e:
        cfg.dereference()
    assert "filter: 'not_a_filter'" in str(e.value)


def test_dereference_exceptions(caplog, tmp_path):
    """
    Test that dereference handles some standard mistakes.
    """
    logging.getLogger().setLevel(logging.DEBUG)
    path = tmp_path / "cfg.yaml"
    with open(path, "w", encoding="utf-8") as f:
        print(
            """
divide: '{{ num // nada }}'  # ZeroDivisionError
foo: bar
list_a: [1, 2, 4]
nada: 0
num: 2
soap: '{{ foo }}'
type_prob: '{{ list_a / \"a\" }}'  # TypeError
""",
            file=f,
        )
    cfgobj = core.YAMLConfig(config_path=path)
    cfgobj.dereference()
    logging.info("HELLO")
    raised = [record.message for record in caplog.records if "raised" in record.message]
    assert "ZeroDivisionError" in raised[0]
    assert "TypeError" in raised[1]


@pytest.mark.parametrize(
    "fn,depth", [("FV3_GFS_v16.yaml", 3), ("simple.nml", 2), ("simple2.ini", 2)]
)
def test_dictionary_depth(depth, fn):
    """
    Test that the proper dictionary depth is returned for each file type.
    """
    infile = fixture_path(fn)
    ext = Path(infile).suffix
    cfgobj = help_cfgclass(ext)(infile)
    assert cfgobj.dictionary_depth(cfgobj.data) == depth


def test_nml_config_simple(salad_base, tmp_path):
    """
    Test that namelist load, update, and dump work with a basic namelist file.
    """
    infile = fixture_path("simple.nml")
    outfile = tmp_path / "outfile.nml"
    cfgobj = core.NMLConfig(infile)
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
        core.create_config_obj(input_base_file=fixture_path("model_configure.sample"))


def test_ini_config_bash(salad_base, tmp_path):
    """
    Test that INI config load and dump work with a basic bash file.
    """
    infile = fixture_path("simple.sh")
    outfile = tmp_path / "outfile.sh"
    cfgobj = core.INIConfig(infile, space_around_delimiters=False)
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
    cfgobj = core.INIConfig(infile)
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
    core.create_config_obj(input_base_file=infile, outfile=outfile, output_file_type="NML")
    expected = core.NMLConfig(infile)
    expected_file = tmp_path / "expected.nml"
    expected.dump_file(expected_file)
    assert compare_files(expected_file, outfile)
    with open(outfile, "r", encoding="utf-8") as f:
        assert f.read()[-1] == "\n"


def test_parse_include():
    """
    Test that non-YAML handles !INCLUDE Tags properly.
    """
    cfgobj = core.NMLConfig(fixture_path("include_files.nml"))
    assert cfgobj["config"]["fruit"] == "papaya"
    assert cfgobj["config"]["how_many"] == 17
    assert cfgobj["config"]["meat"] == "beef"
    assert len(cfgobj["config"]) == 5


def test_parse_include_ini():
    """
    Test that non-YAML handles !INCLUDE Tags properly for INI with no sections.
    """
    cfgobj = core.INIConfig(fixture_path("include_files.sh"), space_around_delimiters=False)
    assert cfgobj.get("fruit") == "papaya"
    assert cfgobj.get("how_many") == "17"
    assert cfgobj.get("meat") == "beef"
    assert len(cfgobj) == 5


def test_parse_include_mult_sect():
    """
    Test that non-YAML handles !INCLUDE tags with files that have multiple sections in separate
    file.
    """
    cfgobj = core.NMLConfig(fixture_path("include_files_with_sect.nml"))
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


def test_set_config_dry_run(caplog):
    """
    Test that providing a YAML base file with a dry run flag will print an YAML config file.
    """
    actual = "\n".join(record.message for record in caplog.records)
    infile = fixture_path("fruit_config.yaml")
    yaml_config = core.YAMLConfig(infile)
    yaml_config.dereference_all()
    core.create_config_obj(input_base_file=infile, dry_run=True)
    actual = "\n".join(record.message for record in caplog.records)
    expected = str(yaml_config)
    assert actual == expected


def test_set_config_field_table(tmp_path):
    """
    Test reading a YAML config object and generating a field file table.
    """
    infile = fixture_path("FV3_GFS_v16.yaml")
    outfile = str(tmp_path / "field_table_from_yaml.FV3_GFS")
    core.create_config_obj(input_base_file=infile, outfile=outfile, output_file_type="FieldTable")
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
    with patch.object(builtins, "help") as help_:
        # Since file types match, help() is not called:
        core.create_config_obj(
            input_base_file=fixture_path("FV3_GFS_v16.yaml"),
            outfile="/dev/null",
            show_format=True,
            output_file_type="YAML",
        )
        help_.assert_not_called()
        # But help() is called when the input is YAML and the output FieldTable:
        core.create_config_obj(
            input_base_file=fixture_path("FV3_GFS_v16.yaml"),
            outfile="/dev/null",
            show_format=True,
            output_file_type="FieldTable",
        )
        help_.assert_called_once()


@pytest.mark.parametrize("fmt1", ["INI", "NML", "YAML"])
@pytest.mark.parametrize("fmt2", ["INI", "NML", "YAML"])
def test_transform_config(fmt1, fmt2, tmp_path):
    """
    Test that transforms config objects to objects of other config subclasses.
    """
    ext1, ext2 = [".%s" % ("NML" if x == "NML" else x).lower() for x in (fmt1, fmt2)]
    outfile = tmp_path / f"test_{fmt1.lower()}to{fmt2.lower()}_dump{ext2}"
    reference = fixture_path(f"simple{ext2}")
    cfgin = help_cfgclass(ext1)(fixture_path(f"simple{ext1}"))
    help_cfgclass(ext2).dump_file_from_dict(path=outfile, cfg=cfgin.data)
    with open(reference, "r", encoding="utf-8") as f1:
        reflines = [line.strip().replace("'", "") for line in f1]
    with open(outfile, "r", encoding="utf-8") as f2:
        outlines = [line.strip().replace("'", "") for line in f2]
    for line1, line2 in zip(reflines, outlines):
        assert line1 == line2


def test_values_needed_ini(caplog):
    """
    Test that the values_needed flag logs keys completed, keys containing unfilled Jinja2 templates,
    and keys set to empty.
    """
    logging.getLogger().setLevel(logging.INFO)
    core.create_config_obj(input_base_file=fixture_path("simple3.ini"), values_needed=True)
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

Keys that have unfilled Jinja2 templates:
    salad.how_many: {{amount}}
    dessert.flavor: {{flavor}}

Keys that are set to empty:
    salad.toppings
    salad.meat
""".strip()
    actual = "\n".join(record.message for record in caplog.records)
    assert actual == expected


def test_values_needed_nml(caplog):
    """
    Test that the values_needed flag logs keys completed, keys containing unfilled Jinja2 templates,
    and keys set to empty.
    """
    logging.getLogger().setLevel(logging.INFO)
    core.create_config_obj(input_base_file=fixture_path("simple3.nml"), values_needed=True)
    expected = """
Keys that are complete:
    salad
    salad.base
    salad.fruit
    salad.vegetable
    salad.how_many
    salad.extras
    salad.dessert

Keys that have unfilled Jinja2 templates:
    salad.dressing: {{ dressing }}

Keys that are set to empty:
    salad.toppings
    salad.appetizer
""".strip()
    actual = "\n".join(record.message for record in caplog.records)
    assert actual == expected


def test_values_needed_yaml(caplog):
    """
    Test that the values_needed flag logs keys completed, keys containing unfilled Jinja2 templates,
    and keys set to empty.
    """
    logging.getLogger().setLevel(logging.INFO)
    core.create_config_obj(input_base_file=fixture_path("srw_example.yaml"), values_needed=True)
    actual = "\n".join(record.message for record in caplog.records)
    expected = """
Keys that are complete:
    FV3GFS
    FV3GFS.nomads
    FV3GFS.nomads.protocol
    FV3GFS.nomads.file_names
    FV3GFS.nomads.file_names.grib2
    FV3GFS.nomads.file_names.testfalse
    FV3GFS.nomads.file_names.testzero

Keys that have unfilled Jinja2 templates:
    FV3GFS.nomads.url: https://nomads.ncep.noaa.gov/pub/data/nccf/com/gfs/prod/gfs.{{ yyyymmdd }}/{{ hh }}/atmos
    FV3GFS.nomads.file_names.grib2.anl: ['gfs.t{{ hh }}z.atmanl.nemsio','gfs.t{{ hh }}z.sfcanl.nemsio']
    FV3GFS.nomads.file_names.grib2.fcst: ['gfs.t{{ hh }}z.pgrb2.0p25.f{{ fcst_hr03d }}']

Keys that are set to empty:
    FV3GFS.nomads.file_names.nemsio
    FV3GFS.nomads.testempty
""".strip()
    assert actual == expected


def test_yaml_config_composite_types():
    """
    Test that YAML load and dump work with a YAML file that has multiple data structures and levels.
    """
    cfgobj = core.YAMLConfig(fixture_path("result4.yaml"))

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
    cfgobj = core.YAMLConfig(fixture_path("include_files.yaml"))

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
    cfgobj = core.YAMLConfig(infile)
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
        core.YAMLConfig(tmpfile)
    assert "value is enclosed in quotes" in str(e.value)


def test_yaml_constructor_error_unregistered_constructor(tmp_path):
    # Test that unregistered constructor raises UWConfigError.

    tmpfile = tmp_path / "test.yaml"
    with tmpfile.open("w", encoding="utf-8") as f:
        f.write("foo: !not_a_constructor bar")
    with raises(exceptions.UWConfigError) as e:
        core.YAMLConfig(tmpfile)
    assert "constructor: '!not_a_constructor'" in str(e.value)
    assert "Define the constructor before proceeding" in str(e.value)


@fixture
def nml_cfgobj(tmp_path):
    # Use NMLConfig to exercise methods in Config abstract base class.
    path = tmp_path / "cfg.nml"
    with open(path, "w", encoding="utf-8") as f:
        f.write("&nl n = 88 /")
    return core.NMLConfig(config_path=path)


def test_Config___repr__(capsys, nml_cfgobj):
    print(nml_cfgobj)
    assert yaml.safe_load(capsys.readouterr().out)["nl"]["n"] == 88


def test_Config_dereference_unexpected_error(nml_cfgobj):
    exctype = FloatingPointError
    with patch.object(core.J2Template, "render_template", side_effect=exctype):
        with raises(exctype):
            nml_cfgobj.dereference(ref_dict={"n": "{{ n }}"})


def test_Config_from_ordereddict(nml_cfgobj):
    d: dict[Any, Any] = OrderedDict([("z", 26), ("a", OrderedDict([("alpha", 1)]))])
    d = nml_cfgobj.from_ordereddict(d)
    # Assert that every OrderedDict is now just a dict. The second assert is needed because
    # isinstance(OrderedDict(), dict) is True.
    for x in d, d["a"]:
        assert isinstance(x, dict)
        assert not isinstance(x, OrderedDict)


def test_Config_iterate_values(nml_cfgobj):
    empty_var: List[str] = []
    jinja2_var: List[str] = []
    set_var: List[str] = []
    d = {1: "", 2: None, 3: "{{ n }}", 4: {"a": 88}, 5: [{"b": 99}], 6: "string"}
    nml_cfgobj.iterate_values(
        config_dict=d, empty_var=empty_var, jinja2_var=jinja2_var, set_var=set_var, parent="p"
    )
    assert empty_var == ["    p1", "    p2"]
    assert jinja2_var == ["    p3: {{ n }}"]
    assert set_var == ["    p4", "    p4.a", "    p5", "    pb", "    p6"]


def test_Config_str_to_type(nml_cfgobj):
    for x in ["true", "yes", "yeah"]:
        assert nml_cfgobj.str_to_type(x) is True
    for x in ["false", "no", "nope"]:
        assert nml_cfgobj.str_to_type(x) is False
    assert nml_cfgobj.str_to_type("88") == 88
    assert nml_cfgobj.str_to_type("3.14") == 3.14
    assert nml_cfgobj.str_to_type("NA") == "NA"  # no conversion


def test_YAMLConfig__load_unexpected_error(tmp_path):
    cfgfile = tmp_path / "cfg.yaml"
    with open(cfgfile, "w", encoding="utf-8") as f:
        print("{n: 88}", file=f)
    with patch.object(core.yaml, "load") as load:
        msg = "Unexpected error"
        load.side_effect = yaml.constructor.ConstructorError(note=msg)
        with raises(UWConfigError) as e:
            core.YAMLConfig(config_path=cfgfile)
        assert msg in str(e.value)


def test_YAMLConfig__load_paths_failure_stdin_plus_relpath(caplog):
    # Instantiate a YAMLConfig with no input file, triggering a read from stdin. Patch stdin to
    # provide YAML with an !INCLUDE directive specifying a relative path. Since a relative path
    # is meaningless relative to stdin, assert that an appropriate error is logged and exception
    # raised.

    relpath = "../bar/baz.yaml"
    with patch.object(core.sys, "stdin", new=StringIO(f"foo: !INCLUDE [{relpath}]")):
        with raises(UWConfigError) as e:
            core.YAMLConfig()
    msg = f"Reading from stdin, a relative path was encountered: {relpath}"
    assert msg in str(e.value)
    assert logged(caplog, msg)


def test_print_config_section_ini(capsys):
    config_obj = core.INIConfig(fixture_path("simple3.ini"))
    section = ["dessert"]
    core.print_config_section(config_obj.data, section)
    actual = capsys.readouterr().out
    expected = """
flavor={{flavor}}
servings=0
side=False
type=pie
""".lstrip()
    assert actual == expected


def test_print_config_section_ini_missing_section():
    config_obj = core.INIConfig(fixture_path("simple3.ini"))
    section = ["sandwich"]
    msg = "Bad config path: sandwich"
    with raises(UWConfigError) as e:
        core.print_config_section(config_obj.data, section)
    assert msg in str(e.value)


def test_print_config_section_yaml(capsys):
    config_obj = core.YAMLConfig(fixture_path("FV3_GFS_v16.yaml"))
    section = ["sgs_tke", "profile_type"]
    core.print_config_section(config_obj.data, section)
    actual = capsys.readouterr().out
    expected = """
name=fixed
surface_value=0.0
""".lstrip()
    assert actual == expected


def test_print_config_section_yaml_for_nonscalar():
    config_obj = core.YAMLConfig(fixture_path("FV3_GFS_v16.yaml"))
    section = ["o3mr"]
    with raises(UWConfigError) as e:
        core.print_config_section(config_obj.data, section)
    assert "Non-scalar value" in str(e.value)


def test_print_config_section_yaml_list():
    config_obj = core.YAMLConfig(fixture_path("srw_example.yaml"))
    section = ["FV3GFS", "nomads", "file_names", "grib2", "anl"]
    with raises(UWConfigError) as e:
        core.print_config_section(config_obj.data, section)
    assert "must be a dictionary" in str(e.value)


def test_print_config_section_yaml_not_dict():
    config_obj = core.YAMLConfig(fixture_path("FV3_GFS_v16.yaml"))
    section = ["sgs_tke", "units"]
    with raises(UWConfigError) as e:
        core.print_config_section(config_obj.data, section)
    assert "must be a dictionary" in str(e.value)


def test__log_and_error():
    with raises(UWConfigError) as e:
        core._log_and_error("Must be scalar value")
    assert "Must be scalar value" in str(e.value)
