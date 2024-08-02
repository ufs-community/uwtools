# pylint: disable=missing-function-docstring,protected-access,redefined-outer-name
"""
Tests for uwtools.config.tools module.
"""

import logging
import sys
from io import StringIO
from pathlib import Path
from textwrap import dedent
from unittest.mock import patch

import f90nml  # type: ignore
import yaml
from pytest import fixture, mark, raises

from uwtools.config import tools
from uwtools.config.formats.ini import INIConfig
from uwtools.config.formats.nml import NMLConfig
from uwtools.config.formats.sh import SHConfig
from uwtools.config.formats.yaml import YAMLConfig
from uwtools.config.support import depth
from uwtools.exceptions import UWConfigError, UWError
from uwtools.logging import log
from uwtools.strings import FORMAT
from uwtools.tests.support import compare_files, fixture_path, logged
from uwtools.utils.file import _stdinproxy as stdinproxy
from uwtools.utils.file import writable

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
    return YAMLConfig(config=realize_config_yaml_input)


@fixture
def realize_config_yaml_input(tmp_path):
    path = tmp_path / "a.yaml"
    d = {1: {2: {3: 88}}}  # depth 3
    with writable(path) as f:
        yaml.dump(d, f)
    return path


# Helpers


def help_realize_config_fmt2fmt(input_file, input_format, update_file, update_format, tmpdir):
    input_file = fixture_path(input_file)
    update_file = fixture_path(update_file)
    ext = Path(input_file).suffix
    output_file = tmpdir / f"output_file{ext}"
    tools.realize_config(
        input_config=input_file,
        input_format=input_format,
        update_config=update_file,
        update_format=update_format,
        output_file=output_file,
        output_format=input_format,
    )
    cfgclass = tools.format_to_config(input_format)
    cfgobj = cfgclass(input_file)
    cfgobj.update_values(cfgclass(update_file))
    reference = tmpdir / f"expected{ext}"
    cfgobj.dump(reference)
    assert compare_files(reference, output_file)


def help_realize_config_simple(infn, infmt, tmpdir):
    infile = fixture_path(infn)
    ext = Path(infile).suffix
    outfile = tmpdir / f"outfile{ext}"
    tools.realize_config(
        input_config=infile,
        input_format=infmt,
        output_file=outfile,
        output_format=infmt,
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
        config_1_path=a, config_1_format=FORMAT.yaml, config_2_path=b, config_2_format=FORMAT.yaml
    )
    assert caplog.records


def test_compare_configs_changed_value(compare_configs_assets, caplog):
    log.setLevel(logging.INFO)
    d, a, b = compare_configs_assets
    d["baz"]["qux"] = 11
    with writable(b) as f:
        yaml.dump(d, f)
    assert not tools.compare_configs(
        config_1_path=a, config_1_format=FORMAT.yaml, config_2_path=b, config_2_format=FORMAT.yaml
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
        config_1_path=b, config_1_format=FORMAT.yaml, config_2_path=a, config_2_format=FORMAT.yaml
    )
    assert logged(caplog, "baz:             qux:  - None + 99")


def test_compare_configs_bad_format(caplog):
    log.setLevel(logging.INFO)
    assert not tools.compare_configs(
        config_1_path=Path("/not/used"),
        config_1_format="jpg",
        config_2_path=Path("/not/used"),
        config_2_format=FORMAT.yaml,
    )
    msg = "Formats do not match: jpg vs yaml"
    assert logged(caplog, msg)


def test_config_check_depths_realize_fail(realize_config_testobj):
    depthin = depth(realize_config_testobj.data)
    with raises(UWConfigError) as e:
        tools.config_check_depths_realize(
            config_obj=realize_config_testobj, target_format=FORMAT.ini
        )
    assert f"Cannot realize depth-{depthin} config to type-'ini' config" in str(e.value)


def test_config_check_depths_update_fail(realize_config_testobj):
    depthin = depth(realize_config_testobj.data)
    with raises(UWConfigError) as e:
        tools.config_check_depths_update(
            config_obj=realize_config_testobj, target_format=FORMAT.ini
        )
    assert f"Cannot update depth-{depthin} config to type-'ini' config" in str(e.value)


def test_realize_config_conversion_cfg_to_yaml(tmp_path):
    """
    Test that a .cfg file can be used to create a YAML object.
    """
    infile = fixture_path("srw_example_yaml.cfg")
    outfile = tmp_path / "test_ouput.yaml"
    tools.realize_config(
        input_config=infile,
        input_format=FORMAT.yaml,
        output_file=outfile,
        output_format=FORMAT.yaml,
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
            input_config=realize_config_yaml_input,
            input_format=FORMAT.yaml,
            output_format=FORMAT.ini,
        )


def test_realize_config_depth_mismatch_to_sh(realize_config_yaml_input):
    with raises(UWConfigError):
        tools.realize_config(
            input_config=realize_config_yaml_input,
            input_format=FORMAT.yaml,
            output_format=FORMAT.sh,
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
        input_config=infile,
        input_format=FORMAT.yaml,
        output_format=FORMAT.yaml,
        dry_run=True,
    )
    actual = "\n".join(record.message for record in caplog.records)
    expected = str(yaml_config).strip()
    assert actual == expected


def test_realize_config_field_table(tmp_path):
    """
    Test reading a YAML config object and generating a field file table.
    """
    infile = fixture_path("FV3_GFS_v16.yaml")
    outfile = tmp_path / "field_table_from_yaml.FV3_GFS"
    tools.realize_config(
        input_config=infile,
        input_format=FORMAT.yaml,
        output_file=outfile,
        output_format=FORMAT.fieldtable,
    )
    with open(fixture_path("field_table.FV3_GFS_v16"), "r", encoding="utf-8") as f1:
        with open(outfile, "r", encoding="utf-8") as f2:
            reflist = [line.rstrip("\n").strip().replace("'", "") for line in f1]
            outlist = [line.rstrip("\n").strip().replace("'", "") for line in f2]
            lines = zip(outlist, reflist)
            for line1, line2 in lines:
                assert line1 in line2


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
    with raises(UWError):
        tools.realize_config(
            input_config=fixture_path("model_configure.sample"),
            input_format="sample",
            output_format=FORMAT.yaml,
        )


def test_realize_config_output_file_format(tmp_path):
    """
    Test that output_format overrides bad output_file extension.
    """
    infile = fixture_path("simple.nml")
    outfile = tmp_path / "test_ouput.cfg"
    tools.realize_config(
        input_config=infile,
        output_file=outfile,
        output_format=FORMAT.nml,
    )
    assert compare_files(outfile, infile)


def test_realize_config_remove_nml_to_nml(tmp_path):
    input_config = NMLConfig({"constants": {"pi": 3.141, "e": 2.718}})
    s = """
    constants:
      e: !remove
    """
    update_config = tmp_path / "update.yaml"
    with open(update_config, "w", encoding="utf-8") as f:
        print(dedent(s).strip(), file=f)
    output_file = tmp_path / "config.nml"
    assert not output_file.is_file()
    tools.realize_config(
        input_config=input_config,
        update_config=update_config,
        output_file=output_file,
    )
    assert f90nml.read(output_file) == {"constants": {"pi": 3.141}}


def test_realize_config_remove_yaml_to_yaml_scalar(tmp_path):
    input_config = YAMLConfig({"a": {"b": {"c": 11, "d": 22, "e": 33}}})
    s = """
    a:
      b:
        d: !remove
    """
    update_config = tmp_path / "update.yaml"
    with open(update_config, "w", encoding="utf-8") as f:
        print(dedent(s).strip(), file=f)
    assert {"a": {"b": {"c": 11, "e": 33}}} == tools.realize_config(
        input_config=input_config,
        update_config=update_config,
        output_format=FORMAT.yaml,
    )


def test_realize_config_remove_yaml_to_yaml_subtree(tmp_path):
    input_config = YAMLConfig(yaml.safe_load("a: {b: {c: 11, d: 22, e: 33}}"))
    s = """
    a:
      b: !remove
    """
    update_config = tmp_path / "update.yaml"
    with open(update_config, "w", encoding="utf-8") as f:
        print(dedent(s).strip(), file=f)
    assert {"a": {}} == tools.realize_config(
        input_config=input_config,
        update_config=update_config,
        output_format=FORMAT.yaml,
    )


def test_realize_config_scalar_value(capsys):
    stdinproxy.cache_clear()
    tools.realize_config(
        input_config=YAMLConfig(config={"foo": {"bar": "baz"}}),
        output_format="yaml",
        key_path=["foo", "bar"],
    )
    assert capsys.readouterr().out.strip() == "baz"


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


def test_realize_config_single_dereference(capsys, tmp_path):
    input_config = tmp_path / "a.yaml"
    update_config = tmp_path / "b.yaml"
    with writable(input_config) as f:
        yaml.dump({"1": "a", "2": "{{ deref }}", "3": "{{ temporalis }}"}, f)
    with writable(update_config) as f:
        yaml.dump({"2": "b", "temporalis": "c", "deref": "d"}, f)
    tools.realize_config(
        input_config=input_config,
        update_config=update_config,
        output_format=FORMAT.yaml,
    )
    actual = capsys.readouterr().out.strip()
    expected = """
    '1': a
    '2': b
    '3': c
    deref: d
    temporalis: c
    """
    assert actual == dedent(expected).strip()


def test_realize_config_update_bad_format(tmp_path):
    input_config = tmp_path / "a.yaml"
    update_config = tmp_path / "b.clj"
    with writable(input_config) as f:
        yaml.dump({"1": "a", "2": "{{ deref }}", "3": "{{ temporalis }}", "deref": "b"}, f)
    with writable(update_config) as f:
        yaml.dump({"2": "b", "temporalis": "c"}, f)
    with raises(UWError) as e:
        tools.realize_config(
            input_config=input_config,
            update_config=update_config,
            output_format=FORMAT.yaml,
            dry_run=True,
        )
    msg = f"Cannot deduce format of '{update_config}' from unknown extension 'clj'"
    assert msg in str(e.value)


def test_realize_config_update_none(capsys, tmp_path):
    path = tmp_path / "a.yaml"
    with writable(path) as f:
        yaml.dump({"1": "a", "2": "{{ deref }}", "3": "{{ temporalis }}", "deref": "b"}, f)
    tools.realize_config(
        input_config=path,
        input_format=FORMAT.yaml,
        output_format=FORMAT.yaml,
    )
    expected = """
    '1': a
    '2': b
    '3': '{{ temporalis }}'
    deref: b
    """
    actual = capsys.readouterr().out.strip()
    assert actual == dedent(expected).strip()


def test_realize_config_total_fail():
    with raises(UWConfigError) as e:
        tools.realize_config(
            input_config=YAMLConfig({"foo": "{{ bar }}"}), output_format=FORMAT.yaml, total=True
        )
    assert str(e.value) == "Config could not be totally realized"


def test_realize_config_values_needed_ini(caplog):
    """
    Test that the values_needed flag logs keys completed and keys containing unrendered Jinja2
    variables/expressions.
    """
    log.setLevel(logging.INFO)
    tools.realize_config(
        input_config=fixture_path("simple3.ini"),
        input_format=FORMAT.ini,
        output_format=FORMAT.ini,
        values_needed=True,
    )
    actual = "\n".join(record.message for record in caplog.records)
    expected = """
    Keys that are complete:
      salad
      salad.base
      salad.fruit
      salad.vegetable
      salad.dressing
      salad.toppings
      salad.meat
      dessert
      dessert.type
      dessert.side
      dessert.servings

    Keys with unrendered Jinja2 variables/expressions:
      salad.how_many: {{ amount }}
      dessert.flavor: {{ flavor }}
    """
    assert actual.strip() == dedent(expected).strip()


def test_realize_config_values_needed_yaml(caplog):
    """
    Test that the values_needed flag logs keys completed and keys containing unrendered Jinja2
    variables/expressions.
    """
    log.setLevel(logging.INFO)
    tools.realize_config(
        input_config=fixture_path("srw_example.yaml"),
        input_format=FORMAT.yaml,
        output_format=FORMAT.yaml,
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
      FV3GFS.nomads.file_names.nemsio
      FV3GFS.nomads.file_names.testfalse
      FV3GFS.nomads.file_names.testzero
      FV3GFS.nomads.testempty

    Keys with unrendered Jinja2 variables/expressions:
      FV3GFS.nomads.url: https://nomads.ncep.noaa.gov/pub/data/nccf/com/gfs/prod/gfs.{{ yyyymmdd }}/{{ hh }}/atmos
      FV3GFS.nomads.file_names.grib2.anl: ['gfs.t{{ hh }}z.atmanl.nemsio', 'gfs.t{{ hh }}z.sfcanl.nemsio']
      FV3GFS.nomads.file_names.grib2.fcst: ['gfs.t{{ hh }}z.pgrb2.0p25.f{{ fcst_hr03d }}']
    """
    assert actual.strip() == dedent(expected).strip()


@mark.skip("PM FIXME")
def test_walk_key_path():
    pass


def test__ensure_format_bad_no_path_no_format():
    with raises(UWError) as e:
        tools._ensure_format(desc="foo")
    assert str(e.value) == "Either foo path or format name must be specified"


def test__ensure_format_config_obj():
    config = NMLConfig({"nl": {"n": 88}})
    assert tools._ensure_format(desc="foo", config=config) == FORMAT.nml


def test__ensure_format_dict_explicit():
    assert tools._ensure_format(desc="foo", fmt=FORMAT.yaml, config={}) == FORMAT.yaml


def test__ensure_format_dict_implicit():
    assert tools._ensure_format(desc="foo", config={}) == FORMAT.yaml


def test__ensure_format_deduced():
    assert tools._ensure_format(desc="foo", config=Path("/tmp/config.nml")) == FORMAT.nml


def test__ensure_format_explicitly_specified_no_path():
    assert tools._ensure_format(desc="foo", fmt=FORMAT.ini) == FORMAT.ini


def test__ensure_format_explicitly_specified_with_path():
    assert (
        tools._ensure_format(desc="foo", fmt=FORMAT.ini, config=Path("/tmp/config.yaml"))
        == FORMAT.ini
    )


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
    """
    assert actual.strip() == dedent(expected).strip()


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
    """
    assert actual.strip() == dedent(expected).strip()


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


def test__realize_config_input_setup_ini_cfgobj():
    data = {"section": {"foo": "bar"}}
    cfgobj = INIConfig(config=data)
    input_obj = tools._realize_config_input_setup(input_config=cfgobj)
    assert input_obj.data == data


def test__realize_config_input_setup_ini_file(tmp_path):
    data = """
    [section]
    foo = bar
    """
    path = tmp_path / "config.ini"
    with open(path, "w", encoding="utf-8") as f:
        print(dedent(data).strip(), file=f)
    input_obj = tools._realize_config_input_setup(input_config=path)
    assert input_obj.data == {"section": {"foo": "bar"}}


def test__realize_config_input_setup_ini_stdin(caplog):
    data = """
    [section]
    foo = bar
    baz = 88
    """
    stdinproxy.cache_clear()
    log.setLevel(logging.DEBUG)
    with StringIO() as sio:
        print(dedent(data).strip(), file=sio)
        sio.seek(0)
        with patch.object(sys, "stdin", new=sio):
            input_obj = tools._realize_config_input_setup(input_format=FORMAT.ini)
    assert input_obj.data == {"section": {"foo": "bar", "baz": "88"}}  # note: 88 is str, not int
    assert logged(caplog, "Reading input from stdin")


def test__realize_config_input_setup_nml_cfgobj():
    data = {"nl": {"pi": 3.14}}
    cfgobj = NMLConfig(config=data)
    input_obj = tools._realize_config_input_setup(input_config=cfgobj)
    assert input_obj.data == data


def test__realize_config_input_setup_nml_file(tmp_path):
    data = """
    &nl
      pi = 3.14
    /
    """
    path = tmp_path / "config.nml"
    with open(path, "w", encoding="utf-8") as f:
        print(dedent(data).strip(), file=f)
    input_obj = tools._realize_config_input_setup(input_config=path)
    assert input_obj["nl"]["pi"] == 3.14


def test__realize_config_input_setup_nml_stdin(caplog):
    data = """
    &nl
      pi = 3.14
    /
    """
    stdinproxy.cache_clear()
    log.setLevel(logging.DEBUG)
    with StringIO() as sio:
        print(dedent(data).strip(), file=sio)
        sio.seek(0)
        with patch.object(sys, "stdin", new=sio):
            input_obj = tools._realize_config_input_setup(input_format=FORMAT.nml)
    assert input_obj["nl"]["pi"] == 3.14
    assert logged(caplog, "Reading input from stdin")


def test__realize_config_input_setup_sh_cfgobj():
    data = {"foo": "bar"}
    cfgobj = SHConfig(config=data)
    input_obj = tools._realize_config_input_setup(input_config=cfgobj)
    assert input_obj.data == data


def test__realize_config_input_setup_sh_file(tmp_path):
    data = """
    foo=bar
    """
    path = tmp_path / "config.sh"
    with open(path, "w", encoding="utf-8") as f:
        print(dedent(data).strip(), file=f)
    input_obj = tools._realize_config_input_setup(input_config=path)
    assert input_obj.data == {"foo": "bar"}


def test__realize_config_input_setup_sh_stdin(caplog):
    data = """
    foo=bar
    """
    stdinproxy.cache_clear()
    log.setLevel(logging.DEBUG)
    with StringIO() as sio:
        print(dedent(data).strip(), file=sio)
        sio.seek(0)
        with patch.object(sys, "stdin", new=sio):
            input_obj = tools._realize_config_input_setup(input_format=FORMAT.sh)
    assert input_obj.data == {"foo": "bar"}
    assert logged(caplog, "Reading input from stdin")


def test__realize_config_input_setup_yaml_cfgobj():
    data = {"foo": "bar"}
    cfgobj = YAMLConfig(config=data)
    input_obj = tools._realize_config_input_setup(input_config=cfgobj)
    assert input_obj.data == data


def test__realize_config_input_setup_yaml_file(tmp_path):
    data = """
    foo: bar
    """
    path = tmp_path / "config.yaml"
    with open(path, "w", encoding="utf-8") as f:
        print(dedent(data).strip(), file=f)
    input_obj = tools._realize_config_input_setup(input_config=path)
    assert input_obj.data == {"foo": "bar"}


def test__realize_config_input_setup_yaml_stdin(caplog):
    data = """
    foo: bar
    """
    stdinproxy.cache_clear()
    log.setLevel(logging.DEBUG)
    with StringIO() as sio:
        print(dedent(data).strip(), file=sio)
        sio.seek(0)
        with patch.object(sys, "stdin", new=sio):
            input_obj = tools._realize_config_input_setup(input_format=FORMAT.yaml)
    assert input_obj.data == {"foo": "bar"}
    assert logged(caplog, "Reading input from stdin")


def test__realize_config_output_setup(caplog, tmp_path):
    log.setLevel(logging.DEBUG)
    input_obj = YAMLConfig({"a": {"b": {"foo": "bar"}}})
    output_file = tmp_path / "output.yaml"
    assert tools._realize_config_output_setup(
        input_obj=input_obj, output_file=output_file, key_path=["a", "b"]
    ) == ({"foo": "bar"}, FORMAT.yaml)
    assert logged(caplog, f"Writing output to {output_file}")


def test__realize_config_update_cfgobj(realize_config_testobj):
    assert realize_config_testobj[1][2][3] == 88
    update_config = YAMLConfig(config={1: {2: {3: 99}}})
    o = tools._realize_config_update(input_obj=realize_config_testobj, update_config=update_config)
    assert o[1][2][3] == 99


def test__realize_config_update_stdin(caplog, realize_config_testobj):
    stdinproxy.cache_clear()
    log.setLevel(logging.DEBUG)
    assert realize_config_testobj[1][2][3] == 88
    with StringIO() as sio:
        print("{1: {2: {3: 99}}}", file=sio)
        sio.seek(0)
        with patch.object(sys, "stdin", new=sio):
            o = tools._realize_config_update(
                input_obj=realize_config_testobj, update_format=FORMAT.yaml
            )
    assert o[1][2][3] == 99
    assert logged(caplog, "Reading update from stdin")


def test__realize_config_update_noop(realize_config_testobj):
    assert tools._realize_config_update(input_obj=realize_config_testobj) == realize_config_testobj


def test__realize_config_update_file(realize_config_testobj, tmp_path):
    assert realize_config_testobj[1][2][3] == 88
    values = {1: {2: {3: 99}}}
    update_config = tmp_path / "config.yaml"
    with open(update_config, "w", encoding="utf-8") as f:
        yaml.dump(values, f)
    o = tools._realize_config_update(input_obj=realize_config_testobj, update_config=update_config)
    assert o[1][2][3] == 99


def test__realize_config_values_needed(caplog, tmp_path):
    log.setLevel(logging.INFO)
    path = tmp_path / "a.yaml"
    with writable(path) as f:
        yaml.dump({1: "complete", 2: "{{ jinja2 }}", 3: ""}, f)
    c = YAMLConfig(config=path)
    tools._realize_config_values_needed(input_obj=c)
    msgs = "\n".join(record.message for record in caplog.records)
    assert "Keys that are complete:\n  1" in msgs
    assert "Keys with unrendered Jinja2 variables/expressions:\n  2" in msgs


def test__realize_config_values_needed_negative_results(caplog, tmp_path):
    log.setLevel(logging.INFO)
    path = tmp_path / "a.yaml"
    with writable(path) as f:
        yaml.dump({}, f)
    c = YAMLConfig(config=path)
    tools._realize_config_values_needed(input_obj=c)
    msgs = "\n".join(record.message for record in caplog.records)
    assert "No keys are complete." in msgs
    assert "No keys have unrendered Jinja2 variables/expressions." in msgs


@mark.parametrize("input_fmt", FORMAT.extensions())
@mark.parametrize("other_fmt", FORMAT.extensions())
def test__validate_format(input_fmt, other_fmt):
    call = lambda: tools._validate_format(
        other_fmt_desc="other", other_fmt=other_fmt, input_fmt=input_fmt
    )
    if FORMAT.yaml in (input_fmt, other_fmt) or input_fmt == other_fmt:
        call()  # no exception raised
    else:
        with raises(UWError) as e:
            call()
        assert str(e.value) == "Accepted other formats for input format {x} are {x} or yaml".format(
            x=input_fmt
        )
