# pylint: disable=duplicate-code,missing-function-docstring,protected-access,redefined-outer-name
"""
Tests for uwtools.config module.
"""

import datetime
import filecmp
import logging
import os
from collections import OrderedDict
from io import StringIO
from pathlib import Path
from typing import Any, Dict
from unittest.mock import patch

import pytest
import yaml
from pytest import fixture, raises

from uwtools import exceptions
from uwtools.config import core
from uwtools.exceptions import UWConfigError
from uwtools.tests.support import compare_files, fixture_path, logged
from uwtools.utils.file import FORMAT, path_if_it_exists, writable

# Test functions


@pytest.mark.parametrize("fmt", [FORMAT.ini, FORMAT.nml, FORMAT.yaml])
def test_compare_config(caplog, fmt, salad_base):
    """
    Compare two config objects.
    """
    logging.getLogger().setLevel(logging.INFO)
    cfgobj = core.format_to_config(fmt)(fixture_path(f"simple.{fmt}"))
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


def test_compare_configs_good(caplog, compare_configs_assets):
    _, a, b = compare_configs_assets
    assert core.compare_configs(
        config_a_path=a, config_a_format=FORMAT.yaml, config_b_path=b, config_b_format=FORMAT.yaml
    )
    assert caplog.records


def test_compare_configs_changed_value(caplog, compare_configs_assets):
    d, a, b = compare_configs_assets
    d["baz"]["qux"] = 11
    with writable(b) as f:
        yaml.dump(d, f)
    assert not core.compare_configs(
        config_a_path=a, config_a_format=FORMAT.yaml, config_b_path=b, config_b_format=FORMAT.yaml
    )
    assert logged(caplog, "baz:             qux:  - 99 + 11")


def test_compare_configs_missing_key(caplog, compare_configs_assets):
    d, a, b = compare_configs_assets
    del d["baz"]
    with writable(b) as f:
        yaml.dump(d, f)
    # Note that a and b are swapped:
    assert not core.compare_configs(
        config_a_path=b, config_a_format=FORMAT.yaml, config_b_path=a, config_b_format=FORMAT.yaml
    )
    assert logged(caplog, "baz:             qux:  - None + 99")


def test_compare_configs_bad_format(caplog):
    logging.getLogger().setLevel(logging.INFO)
    with raises(UWConfigError) as e:
        core.compare_configs(
            config_a_path="/not/used",
            config_a_format="jpg",
            config_b_path="/not/used",
            config_b_format=FORMAT.yaml,
        )
    msg = "Format 'jpg' should be one of: fieldtable, ini, nml, yaml"
    assert logged(caplog, msg)
    assert msg in str(e.value)


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


@pytest.mark.parametrize(
    "fn,depth", [("FV3_GFS_v16.yaml", 3), ("simple.nml", 2), ("simple2.ini", 2)]
)
def test_depth(depth, fn):
    """
    Test that the proper dictionary depth is returned for each file type.
    """
    infile = fixture_path(fn)
    fmt = Path(infile).suffix.replace(".", "")
    cfgobj = core.format_to_config(fmt)(infile)
    assert cfgobj._depth(cfgobj.data) == depth


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
    cfg = core.YAMLConfig(config_file=path)
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
    cfgobj = core.YAMLConfig(config_file=path)
    cfgobj.dereference()
    logging.info("HELLO")
    raised = [record.message for record in caplog.records if "raised" in record.message]
    assert "ZeroDivisionError" in raised[0]
    assert "TypeError" in raised[1]


def test_ini_config_bash(salad_base, tmp_path):
    """
    Test that INI config load and dump work with a basic bash file.
    """
    infile = fixture_path("simple.sh")
    outfile = tmp_path / "outfile.sh"
    cfgobj = core.INIConfig(infile, space_around_delimiters=False)
    expected: Dict[str, Any] = {
        **salad_base["salad"],
        "how_many": "12",
    }  # str "12" (not int 12) for INI
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


def test_realize_config_conversion_cfg_to_yaml(tmp_path):
    """
    Test that a .cfg file can be used to create a YAML object.
    """
    infile = fixture_path("srw_example_yaml.cfg")
    outfile = str(tmp_path / "test_ouput.yaml")
    core.realize_config(
        input_file=infile,
        input_format=FORMAT.yaml,
        output_file=outfile,
        output_format=FORMAT.yaml,
        values_file=None,
        values_format=None,
    )
    expected = core.YAMLConfig(infile)
    expected.dereference_all()
    expected_file = tmp_path / "test.yaml"
    expected.dump_file(expected_file)
    assert compare_files(expected_file, outfile)
    with open(outfile, "r", encoding="utf-8") as f:
        assert f.read()[-1] == "\n"


def test_realize_config_depth_mismatch_to_ini(realize_config_yaml_input):
    with raises(UWConfigError):
        core.realize_config(
            input_file=realize_config_yaml_input,
            input_format=FORMAT.yaml,
            output_file=None,
            output_format=FORMAT.ini,
            values_file=None,
            values_format=None,
        )


def test_realize_config_depth_mismatch_to_nml(realize_config_yaml_input):
    with raises(UWConfigError):
        core.realize_config(
            input_file=realize_config_yaml_input,
            input_format=FORMAT.yaml,
            output_file=None,
            output_format=FORMAT.nml,
            values_file=None,
            values_format=None,
        )


def test_realize_config_dry_run(caplog):
    """
    Test that providing a YAML base file with a dry-run flag will print an YAML config file.
    """
    logging.getLogger().setLevel(logging.INFO)
    infile = fixture_path("fruit_config.yaml")
    yaml_config = core.YAMLConfig(infile)
    yaml_config.dereference_all()
    core.realize_config(
        input_file=infile,
        input_format=FORMAT.yaml,
        output_file=None,
        output_format=FORMAT.yaml,
        values_file=None,
        values_format=None,
        dry_run=True,
    )
    actual = "\n".join(record.message for record in caplog.records)
    expected = str(yaml_config)
    assert actual == expected


def test_realize_config_field_table(tmp_path):
    """
    Test reading a YAML config object and generating a field file table.
    """
    infile = fixture_path("FV3_GFS_v16.yaml")
    outfile = str(tmp_path / "field_table_from_yaml.FV3_GFS")
    core.realize_config(
        input_file=infile,
        input_format=FORMAT.yaml,
        output_file=outfile,
        output_format="fieldtable",
        values_file=None,
        values_format=None,
    )
    with open(fixture_path("field_table.FV3_GFS_v16"), "r", encoding="utf-8") as f1:
        with open(outfile, "r", encoding="utf-8") as f2:
            reflist = [line.rstrip("\n").strip().replace("'", "") for line in f1]
            outlist = [line.rstrip("\n").strip().replace("'", "") for line in f2]
            lines = zip(outlist, reflist)
            for line1, line2 in lines:
                assert line1 in line2


def test_realize_config_file_conversion(tmp_path):
    """
    Test using an ini object to configure nml input -> nml output.
    """
    infile = fixture_path("simple2.nml")
    cfgfile = fixture_path("simple2.ini")
    outfile = str(tmp_path / "test_config_conversion.nml")
    core.realize_config(
        input_file=infile,
        input_format=FORMAT.nml,
        output_file=outfile,
        output_format=FORMAT.nml,
        values_file=cfgfile,
        values_format=FORMAT.ini,
    )
    expected = core.NMLConfig(infile)
    config_obj = core.INIConfig(cfgfile)
    expected.update_values(config_obj)
    expected_file = tmp_path / "expected.nml"
    expected.dump_file(expected_file)
    assert compare_files(expected_file, outfile)
    with open(outfile, "r", encoding="utf-8") as f:
        assert f.read()[-1] == "\n"


def test_realize_config_fmt2fmt_nml2nml(tmp_path):
    """
    Test that providing a namelist base input file and a config file will create and update namelist
    config file.
    """
    help_realize_config_fmt2fmt("simple.nml", FORMAT.nml, "simple2.nml", FORMAT.nml, tmp_path)


def test_realize_config_fmt2fmt_ini2bash(tmp_path):
    """
    Test that providing an INI base input file and a Bash config file will create and update INI
    config file.
    """
    help_realize_config_fmt2fmt("simple.ini", FORMAT.ini, "fruit_config.sh", FORMAT.ini, tmp_path)


def test_realize_config_fmt2fmt_ini2ini(tmp_path):
    """
    Test that providing an INI base input file and an INI config file will create and update INI
    config file.
    """
    help_realize_config_fmt2fmt("simple.ini", FORMAT.ini, "simple2.ini", FORMAT.ini, tmp_path)


def test_realize_config_fmt2fmt_yaml2yaml(tmp_path):
    """
    Test that providing a YAML base input file and a YAML config file will create and update YAML
    config file.
    """
    help_realize_config_fmt2fmt(
        "fruit_config.yaml", FORMAT.yaml, "fruit_config_similar.yaml", FORMAT.yaml, tmp_path
    )


def test_realize_config_incompatible_file_type():
    """
    Test that providing an incompatible file type for input base file will return print statement.
    """
    with raises(UWConfigError):
        core.realize_config(
            input_file=fixture_path("model_configure.sample"),
            input_format="sample",
            output_file=None,
            output_format=FORMAT.yaml,
            values_file=None,
            values_format=None,
        )


def test_realize_config_output_file_conversion(tmp_path):
    """
    Test that --output-input-type converts config object to desired object type.
    """
    infile = fixture_path("simple.nml")
    outfile = str(tmp_path / "test_ouput.cfg")
    core.realize_config(
        input_file=infile,
        input_format=FORMAT.nml,
        output_file=outfile,
        output_format=FORMAT.nml,
        values_file=None,
        values_format=None,
    )
    expected = core.NMLConfig(infile)
    expected_file = tmp_path / "expected.nml"
    expected.dump_file(expected_file)
    assert compare_files(expected_file, outfile)
    with open(outfile, "r", encoding="utf-8") as f:
        assert f.read()[-1] == "\n"


def test_realize_config_simple_bash(tmp_path):
    """
    Test that providing a bash file with necessary settings will create an INI config file.
    """
    help_realize_config_simple("simple.sh", FORMAT.ini, tmp_path)


def test_realize_config_simple_namelist(tmp_path):
    """
    Test that providing a namelist file with necessary settings will create a namelist config file.
    """
    help_realize_config_simple("simple.nml", FORMAT.nml, tmp_path)


def test_realize_config_simple_ini(tmp_path):
    """
    Test that providing an INI file with necessary settings will create an INI config file.
    """
    help_realize_config_simple("simple.ini", FORMAT.ini, tmp_path)


def test_realize_config_simple_yaml(tmp_path):
    """
    Test that providing a YAML base file with necessary settings will create a YAML config file.
    """
    help_realize_config_simple("simple2.yaml", FORMAT.yaml, tmp_path)


@pytest.mark.parametrize("fmt", [FORMAT.ini, FORMAT.nml])
def test__realize_config_check_depths_fail_nml(realize_config_testobj, fmt):
    with raises(UWConfigError):
        core._realize_config_check_depths(input_obj=realize_config_testobj, output_format=fmt)


def test__realize_config_update_noop(realize_config_testobj):
    assert realize_config_testobj == core._realize_config_update(
        input_obj=realize_config_testobj, values_file=None, values_format=None
    )


def test__realize_config_update(realize_config_testobj, tmp_path):
    o = realize_config_testobj
    assert o.depth == 3
    path = tmp_path / "values.yaml"
    with writable(path) as f:
        yaml.dump({1: {2: {3: {4: 99}}}}, f)  # depth 4
    o = core._realize_config_update(input_obj=o, values_file=path, values_format=FORMAT.yaml)
    assert o.depth == 4
    assert o[1][2][3][4] == 99


def test__realize_config_values_needed(caplog, tmp_path):
    path = tmp_path / "a.yaml"
    with writable(path) as f:
        yaml.dump({1: "complete", 2: "{{ jinja2 }}", 3: ""}, f)
    c = core.YAMLConfig(config_file=path)
    core._realize_config_values_needed(input_obj=c)
    msgs = "\n".join(record.message for record in caplog.records)
    assert "Keys that are complete:\n    1" in msgs
    assert "Keys that have unfilled Jinja2 templates:\n    2" in msgs
    assert "Keys that are set to empty:\n    3" in msgs


@pytest.mark.parametrize("fmt1", [FORMAT.ini, FORMAT.nml, FORMAT.yaml])
@pytest.mark.parametrize("fmt2", [FORMAT.ini, FORMAT.nml, FORMAT.yaml])
def test_transform_config(fmt1, fmt2, tmp_path):
    """
    Test that transforms config objects to objects of other config subclasses.
    """
    outfile = tmp_path / f"test_{fmt1.lower()}to{fmt2.lower()}_dump.{fmt2}"
    reference = fixture_path(f"simple.{fmt2}")
    cfgin = core.format_to_config(fmt1)(fixture_path(f"simple.{fmt1}"))
    core.format_to_config(fmt2).dump_dict(path=outfile, cfg=cfgin.data)
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
    core.realize_config(
        input_file=fixture_path("simple3.ini"),
        input_format=FORMAT.ini,
        output_file=None,
        output_format=FORMAT.ini,
        values_file=None,
        values_format=None,
        values_needed=True,
    )
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
    core.realize_config(
        input_file=fixture_path("simple3.nml"),
        input_format=FORMAT.nml,
        output_file=None,
        output_format=FORMAT.yaml,
        values_file=None,
        values_format=None,
        values_needed=True,
    )
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
    core.realize_config(
        input_file=fixture_path("srw_example.yaml"),
        input_format=FORMAT.yaml,
        output_file=None,
        output_format=FORMAT.yaml,
        values_file=None,
        values_format=None,
        values_needed=True,
    )
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


def test_Config___repr__(capsys, nml_cfgobj):
    print(nml_cfgobj)
    assert yaml.safe_load(capsys.readouterr().out)["nl"]["n"] == 88


def test_Config_characterize_values(nml_cfgobj):
    d = {1: "", 2: None, 3: "{{ n }}", 4: {"a": 88}, 5: [{"b": 99}], 6: "string"}
    complete, empty, template = nml_cfgobj.characterize_values(values=d, parent="p")
    assert complete == ["    p4", "    p4.a", "    p5", "    pb", "    p6"]
    assert empty == ["    p1", "    p2"]
    assert template == ["    p3: {{ n }}"]


def test_Config_str_to_type(nml_cfgobj):
    for x in ["true", "yes", "yeah"]:
        assert nml_cfgobj.str_to_type(x) is True
    for x in ["false", "no", "nope"]:
        assert nml_cfgobj.str_to_type(x) is False
    assert nml_cfgobj.str_to_type("88") == 88
    assert nml_cfgobj.str_to_type("3.14") == 3.14
    assert nml_cfgobj.str_to_type("NA") == "NA"  # no conversion


def test_Config_dereference_unexpected_error(nml_cfgobj):
    exctype = FloatingPointError
    with patch.object(core.J2Template, "render", side_effect=exctype):
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


def test_YAMLConfig__load_unexpected_error(tmp_path):
    cfgfile = tmp_path / "cfg.yaml"
    with open(cfgfile, "w", encoding="utf-8") as f:
        print("{n: 88}", file=f)
    with patch.object(core.yaml, "load") as load:
        msg = "Unexpected error"
        load.side_effect = yaml.constructor.ConstructorError(note=msg)
        with raises(UWConfigError) as e:
            core.YAMLConfig(config_file=cfgfile)
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


def test__log_and_error():
    with raises(UWConfigError) as e:
        raise core._log_and_error("Must be scalar value")
    assert "Must be scalar value" in str(e.value)


# Helper functions


@fixture
def compare_configs_assets(tmp_path):
    d = {"foo": {"bar": 88}, "baz": {"qux": 99}}
    a = tmp_path / "a"
    b = tmp_path / "b"
    with writable(a) as f:
        yaml.dump(d, f)
    with writable(b) as f:
        yaml.dump(d, f)
    return d, a, b


def help_realize_config_fmt2fmt(infn, infmt, cfgfn, cfgfmt, tmpdir):
    infile = fixture_path(infn)
    cfgfile = fixture_path(cfgfn)
    ext = Path(infile).suffix
    outfile = str(tmpdir / f"outfile{ext}")
    core.realize_config(
        input_file=infile,
        input_format=infmt,
        output_file=outfile,
        output_format=infmt,
        values_file=cfgfile,
        values_format=cfgfmt,
    )
    cfgclass = core.format_to_config(infmt)
    cfgobj = cfgclass(infile)
    cfgobj.update_values(cfgclass(cfgfile))
    reference = tmpdir / "expected"
    cfgobj.dump_file(reference)
    assert compare_files(reference, outfile)


def help_realize_config_simple(infn, infmt, tmpdir):
    infile = fixture_path(infn)
    ext = Path(infile).suffix
    outfile = str(tmpdir / f"outfile{ext}")
    core.realize_config(
        input_file=infile,
        input_format=infmt,
        output_file=outfile,
        output_format=infmt,
        values_file=None,
        values_format=None,
    )
    cfgobj = core.format_to_config(infmt)(infile)
    reference = tmpdir / f"reference{ext}"
    cfgobj.dump_file(reference)
    assert compare_files(reference, outfile)


@fixture
def nml_cfgobj(tmp_path):
    # Use NMLConfig to exercise methods in Config abstract base class.
    path = tmp_path / "cfg.nml"
    with open(path, "w", encoding="utf-8") as f:
        f.write("&nl n = 88 /")
    return core.NMLConfig(config_file=path)


@fixture
def realize_config_testobj(realize_config_yaml_input):
    return core.YAMLConfig(config_file=realize_config_yaml_input)


@fixture
def realize_config_yaml_input(tmp_path):
    path = tmp_path / "a.yaml"
    d = {1: {2: {3: 88}}}  # depth 3
    with writable(path) as f:
        yaml.dump(d, f)
    return path


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
