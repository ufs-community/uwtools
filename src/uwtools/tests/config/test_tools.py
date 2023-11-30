# pylint: disable=missing-function-docstring,protected-access,redefined-outer-name
"""
Tests for uwtools.config.tools module.
"""

import logging
from pathlib import Path

import pytest
import yaml
from pytest import fixture, raises

from uwtools.config import tools
from uwtools.config.formats.ini import INIConfig
from uwtools.config.formats.nml import NMLConfig
from uwtools.config.formats.yaml import YAMLConfig
from uwtools.exceptions import UWConfigError
from uwtools.logging import log
from uwtools.tests.support import compare_files, fixture_path, logged
from uwtools.utils.file import FORMAT, writable

# Fixtures


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


@fixture
def realize_config_testobj(realize_config_yaml_input):
    return YAMLConfig(config_file=realize_config_yaml_input)


@fixture
def realize_config_yaml_input(tmp_path):
    path = tmp_path / "a.yaml"
    d = {1: {2: {3: 88}}}  # depth 3
    with writable(path) as f:
        yaml.dump(d, f)
    return path


# Helpers


def help_realize_config_fmt2fmt(infn, infmt, cfgfn, cfgfmt, tmpdir):
    infile = fixture_path(infn)
    cfgfile = fixture_path(cfgfn)
    ext = Path(infile).suffix
    outfile = str(tmpdir / f"outfile{ext}")
    tools.realize_config(
        input_file=infile,
        input_format=infmt,
        output_file=outfile,
        output_format=infmt,
        values_file=cfgfile,
        values_format=cfgfmt,
    )
    cfgclass = tools.format_to_config(infmt)
    cfgobj = cfgclass(infile)
    cfgobj.update_values(cfgclass(cfgfile))
    reference = tmpdir / "expected"
    cfgobj.dump(reference)
    assert compare_files(reference, outfile)


def help_realize_config_simple(infn, infmt, tmpdir):
    infile = fixture_path(infn)
    ext = Path(infile).suffix
    outfile = str(tmpdir / f"outfile{ext}")
    tools.realize_config(
        input_file=infile,
        input_format=infmt,
        output_file=outfile,
        output_format=infmt,
        values_file=None,
        values_format=None,
    )
    cfgobj = tools.format_to_config(infmt)(infile)
    reference = tmpdir / f"reference{ext}"
    cfgobj.dump(reference)
    assert compare_files(reference, outfile)


# Tests


def test_compare_configs_good(compare_configs_assets, caplog):
    log.setLevel(logging.INFO)
    _, a, b = compare_configs_assets
    assert tools.compare_configs(
        config_a_path=a, config_a_format=FORMAT.yaml, config_b_path=b, config_b_format=FORMAT.yaml
    )
    assert caplog.records


def test_compare_configs_changed_value(compare_configs_assets, caplog):
    log.setLevel(logging.INFO)
    d, a, b = compare_configs_assets
    d["baz"]["qux"] = 11
    with writable(b) as f:
        yaml.dump(d, f)
    assert not tools.compare_configs(
        config_a_path=a, config_a_format=FORMAT.yaml, config_b_path=b, config_b_format=FORMAT.yaml
    )
    assert logged(caplog, "baz:             qux:  - 99 + 11")


def test_compare_configs_missing_key(compare_configs_assets, caplog):
    log.setLevel(logging.INFO)
    d, a, b = compare_configs_assets
    del d["baz"]
    with writable(b) as f:
        yaml.dump(d, f)
    # Note that a and b are swapped:
    assert not tools.compare_configs(
        config_a_path=b, config_a_format=FORMAT.yaml, config_b_path=a, config_b_format=FORMAT.yaml
    )
    assert logged(caplog, "baz:             qux:  - None + 99")


def test_compare_configs_bad_format(caplog):
    log.setLevel(logging.INFO)
    with raises(UWConfigError) as e:
        tools.compare_configs(
            config_a_path="/not/used",
            config_a_format="jpg",
            config_b_path="/not/used",
            config_b_format=FORMAT.yaml,
        )
    msg = "Format 'jpg' should be one of: fieldtable, ini, nml, sh, yaml"
    assert logged(caplog, msg)
    assert msg in str(e.value)


@pytest.mark.parametrize("fmt", ["ini", "sh"])
def test__config_check_depths_fail_sh(fmt, realize_config_testobj):
    with raises(UWConfigError):
        tools.config_check_depths(input_obj=realize_config_testobj, target_format=fmt)


def test_realize_config_conversion_cfg_to_yaml(tmp_path):
    """
    Test that a .cfg file can be used to create a YAML object.
    """
    infile = fixture_path("srw_example_yaml.cfg")
    outfile = str(tmp_path / "test_ouput.yaml")
    tools.realize_config(
        input_file=infile,
        input_format=FORMAT.yaml,
        output_file=outfile,
        output_format=FORMAT.yaml,
        values_file=None,
        values_format=None,
    )
    expected = YAMLConfig(infile)
    expected.dereference()
    expected_file = tmp_path / "test.yaml"
    expected.dump(expected_file)
    assert compare_files(expected_file, outfile)
    with open(outfile, "r", encoding="utf-8") as f:
        assert f.read()[-1] == "\n"


def test_realize_config_depth_mismatch_to_ini(realize_config_yaml_input):
    with raises(UWConfigError):
        tools.realize_config(
            input_file=realize_config_yaml_input,
            input_format=FORMAT.yaml,
            output_file=None,
            output_format=FORMAT.ini,
            values_file=None,
            values_format=None,
        )


def test_realize_config_depth_mismatch_to_sh(realize_config_yaml_input):
    with raises(UWConfigError):
        tools.realize_config(
            input_file=realize_config_yaml_input,
            input_format=FORMAT.yaml,
            output_file=None,
            output_format=FORMAT.sh,
            values_file=None,
            values_format=None,
        )


def test_realize_config_dry_run(caplog):
    """
    Test that providing a YAML base file with a dry-run flag will print an YAML config file.
    """
    log.setLevel(logging.INFO)
    infile = fixture_path("fruit_config.yaml")
    yaml_config = YAMLConfig(infile)
    yaml_config.dereference()
    tools.realize_config(
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
    tools.realize_config(
        input_file=infile,
        input_format=FORMAT.yaml,
        output_file=outfile,
        output_format=FORMAT.fieldtable,
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


@pytest.mark.skip("Updating typed Fortran namelist from untyped INI data is unsound")
def test_realize_config_file_conversion(tmp_path):
    """
    Test using an ini object to configure nml input -> nml output.
    """
    infile = fixture_path("simple2.nml")
    cfgfile = fixture_path("simple2.ini")
    outfile = str(tmp_path / "test_config_conversion.nml")
    tools.realize_config(
        input_file=infile,
        input_format=FORMAT.nml,
        output_file=outfile,
        output_format=FORMAT.nml,
        values_file=cfgfile,
        values_format=FORMAT.ini,
    )
    expected = NMLConfig(infile)
    config_obj = INIConfig(cfgfile)
    expected.update_values(config_obj)
    expected_file = tmp_path / "expected.nml"
    expected.dump(expected_file)
    assert compare_files(expected_file, outfile)
    with open(outfile, "r", encoding="utf-8") as f:
        assert f.read()[-1] == "\n"


def test_realize_config_fmt2fmt_nml2nml(tmp_path):
    """
    Test that providing a namelist base input file and a config file will create and update namelist
    config file.
    """
    help_realize_config_fmt2fmt("simple.nml", FORMAT.nml, "simple2.nml", FORMAT.nml, tmp_path)


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
        tools.realize_config(
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
    tools.realize_config(
        input_file=infile,
        input_format=FORMAT.nml,
        output_file=outfile,
        output_format=FORMAT.nml,
        values_file=None,
        values_format=None,
    )
    expected = NMLConfig(infile)
    expected_file = tmp_path / "expected.nml"
    expected.dump(expected_file)
    assert compare_files(expected_file, outfile)
    with open(outfile, "r", encoding="utf-8") as f:
        assert f.read()[-1] == "\n"


def test_realize_config_simple_ini(tmp_path):
    """
    Test that providing an INI file with necessary settings will create an INI config file.
    """

    help_realize_config_simple("simple.ini", FORMAT.ini, tmp_path)


def test_realize_config_simple_namelist(tmp_path):
    """
    Test that providing a namelist file with necessary settings will create a namelist config file.
    """
    help_realize_config_simple("simple.nml", FORMAT.nml, tmp_path)


def test_realize_config_simple_sh(tmp_path):
    """
    Test that providing an sh file with necessary settings will create an sh config file.
    """
    help_realize_config_simple("simple.sh", FORMAT.sh, tmp_path)


def test_realize_config_simple_yaml(tmp_path):
    """
    Test that providing a YAML base file with necessary settings will create a YAML config file.
    """
    help_realize_config_simple("simple2.yaml", FORMAT.yaml, tmp_path)


def test_realize_config_values_needed_ini(caplog):
    """
    Test that the values_needed flag logs keys completed, keys containing unfilled Jinja2 templates,
    and keys set to empty.
    """
    log.setLevel(logging.INFO)
    tools.realize_config(
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
    salad.how_many: {{ amount }}
    dessert.flavor: {{ flavor }}

Keys that are set to empty:
    salad.toppings
    salad.meat
""".strip()
    actual = "\n".join(record.message for record in caplog.records)
    assert actual == expected


def test_realize_config_values_needed_nml(caplog):
    """
    Test that the values_needed flag logs keys completed, keys containing unfilled Jinja2 templates,
    and keys set to empty.
    """
    log.setLevel(logging.INFO)
    tools.realize_config(
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


def test_realize_config_values_needed_yaml(caplog):
    """
    Test that the values_needed flag logs keys completed, keys containing unfilled Jinja2 templates,
    and keys set to empty.
    """
    log.setLevel(logging.INFO)
    tools.realize_config(
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
    FV3GFS.nomads.file_names.grib2.anl: ['gfs.t{{ hh }}z.atmanl.nemsio', 'gfs.t{{ hh }}z.sfcanl.nemsio']
    FV3GFS.nomads.file_names.grib2.fcst: ['gfs.t{{ hh }}z.pgrb2.0p25.f{{ fcst_hr03d }}']

Keys that are set to empty:
    FV3GFS.nomads.file_names.nemsio
    FV3GFS.nomads.testempty
""".strip()
    assert actual == expected


def test__print_config_section_ini(capsys):
    config_obj = INIConfig(fixture_path("simple3.ini"))
    section = ["dessert"]
    tools._print_config_section(config_obj.data, section)
    actual = capsys.readouterr().out
    expected = """
flavor={{ flavor }}
servings=0
side=False
type=pie
""".lstrip()
    assert actual == expected


def test__print_config_section_ini_missing_section():
    config_obj = INIConfig(fixture_path("simple3.ini"))
    section = ["sandwich"]
    msg = "Bad config path: sandwich"
    with raises(UWConfigError) as e:
        tools._print_config_section(config_obj.data, section)
    assert msg in str(e.value)


def test__print_config_section_yaml(capsys):
    config_obj = YAMLConfig(fixture_path("FV3_GFS_v16.yaml"))
    section = ["sgs_tke", "profile_type"]
    tools._print_config_section(config_obj.data, section)
    actual = capsys.readouterr().out
    expected = """
name=fixed
surface_value=0.0
""".lstrip()
    assert actual == expected


def test__print_config_section_yaml_for_nonscalar():
    config_obj = YAMLConfig(fixture_path("FV3_GFS_v16.yaml"))
    section = ["o3mr"]
    with raises(UWConfigError) as e:
        tools._print_config_section(config_obj.data, section)
    assert "Non-scalar value" in str(e.value)


def test__print_config_section_yaml_list():
    config_obj = YAMLConfig(fixture_path("srw_example.yaml"))
    section = ["FV3GFS", "nomads", "file_names", "grib2", "anl"]
    with raises(UWConfigError) as e:
        tools._print_config_section(config_obj.data, section)
    assert "must be a dictionary" in str(e.value)


def test__print_config_section_yaml_not_dict():
    config_obj = YAMLConfig(fixture_path("FV3_GFS_v16.yaml"))
    section = ["sgs_tke", "units"]
    with raises(UWConfigError) as e:
        tools._print_config_section(config_obj.data, section)
    assert "must be a dictionary" in str(e.value)


def test__realize_config_update_noop(realize_config_testobj):
    assert realize_config_testobj == tools._realize_config_update(
        input_obj=realize_config_testobj, values_file=None, values_format=None
    )


def test__realize_config_update(realize_config_testobj, tmp_path):
    o = realize_config_testobj
    assert o.depth == 3
    path = tmp_path / "values.yaml"
    with writable(path) as f:
        yaml.dump({1: {2: {3: {4: 99}}}}, f)  # depth 4
    o = tools._realize_config_update(input_obj=o, values_file=path, values_format=FORMAT.yaml)
    assert o.depth == 4
    assert o[1][2][3][4] == 99


def test__realize_config_values_needed(caplog, tmp_path):
    log.setLevel(logging.INFO)
    path = tmp_path / "a.yaml"
    with writable(path) as f:
        yaml.dump({1: "complete", 2: "{{ jinja2 }}", 3: ""}, f)
    c = YAMLConfig(config_file=path)
    tools._realize_config_values_needed(input_obj=c)
    msgs = "\n".join(record.message for record in caplog.records)
    assert "Keys that are complete:\n    1" in msgs
    assert "Keys that have unfilled Jinja2 templates:\n    2" in msgs
    assert "Keys that are set to empty:\n    3" in msgs
