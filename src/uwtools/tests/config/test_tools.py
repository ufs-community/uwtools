"""
Tests for uwtools.config.tools module.
"""

import sys
from io import StringIO
from pathlib import Path
from textwrap import dedent
from unittest.mock import patch

import f90nml  # type: ignore[import-untyped]
import yaml
from pytest import fixture, mark, raises

from uwtools.config import tools
from uwtools.config.formats.fieldtable import FieldTableConfig
from uwtools.config.formats.ini import INIConfig
from uwtools.config.formats.nml import NMLConfig
from uwtools.config.formats.sh import SHConfig
from uwtools.config.formats.yaml import YAMLConfig
from uwtools.exceptions import UWConfigError, UWError
from uwtools.strings import FORMAT
from uwtools.tests.support import compare_files, fixture_path
from uwtools.utils.file import _stdinproxy as stdinproxy
from uwtools.utils.file import writable

# Fixtures


@fixture
def compare_assets(tmp_path):
    d = {"foo": {"bar": 42}, "baz": {"qux": 43}}
    a = tmp_path / "a"
    b = tmp_path / "b"
    with writable(a) as f:
        yaml.dump(d, f)
    with writable(b) as f:
        yaml.dump(d, f)
    return d, a, b


@fixture
def compose_assets_yaml():
    d1 = {"k10": "v10", "k11": "v11"}
    u1 = {"k10": "u10", "k12": "v12"}
    d2 = {"k10": {"k21": "v21", "k22": "v22"}, "k11": "v11"}
    u2 = {"k10": {"k21": "u21"}, "k12": "v12"}
    d3 = {"k10": {"k21": {"k31": "v31", "k32": "v32"}, "k22": "v22"}, "k11": "v11"}
    u3 = {"k10": {"k21": {"k31": ["v310", "v311"], "k33": "v33"}}}
    return d1, u1, d2, u2, d3, u3


@fixture
def realize_testobj(realize_yaml_input):
    return YAMLConfig(config=realize_yaml_input)


@fixture
def realize_yaml_input(tmp_path):
    path = tmp_path / "a.yaml"
    d = {1: {2: {3: 42}}}  # depth 3
    with writable(path) as f:
        yaml.dump(d, f)
    return path


# Helpers


def help_realize_double_tag(config, expected, tmp_path):
    path_in = tmp_path / "in.yaml"
    path_out = tmp_path / "out.yaml"
    path_in.write_text(dedent(config).strip())
    tools.realize(input_config=path_in, output_file=path_out)
    assert path_out.read_text().strip() == dedent(expected).strip()


def help_realize_fmt2fmt(input_file, input_format, update_file, update_format, tmpdir):
    input_file = fixture_path(input_file)
    update_file = fixture_path(update_file)
    ext = Path(input_file).suffix
    output_file = tmpdir / f"output_file{ext}"
    tools.realize(
        input_config=input_file,
        input_format=input_format,
        update_config=update_file,
        update_format=update_format,
        output_file=output_file,
        output_format=input_format,
    )
    cfgclass = tools.format_to_config(input_format)
    cfgobj = cfgclass(input_file)
    cfgobj.update_from(cfgclass(update_file))
    reference = tmpdir / f"expected{ext}"
    cfgobj.dump(reference)
    assert compare_files(reference, output_file)


def help_realize_simple(infn, infmt, tmpdir):
    infile = fixture_path(infn)
    ext = Path(infile).suffix
    outfile = tmpdir / f"outfile{ext}"
    tools.realize(
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


def test_config_tools_compare__good(compare_assets, logged):
    _, a, b = compare_assets
    assert tools.compare(path1=a, format1=FORMAT.yaml, path2=b, format2=FORMAT.yaml)
    assert logged(".*", regex=True)


def test_config_tools_compare__changed_value(compare_assets, logged):
    d, a, b = compare_assets
    d["baz"]["qux"] = 11
    with writable(b) as f:
        yaml.dump(d, f)
    assert not tools.compare(path1=a, format1=FORMAT.yaml, path2=b, format2=FORMAT.yaml)
    expected = """
    - %s
    + %s
    ---------------------------------------------------------------------
    ↓ ? = info | -/+ = line unique to - or + file | blank = matching line
    ---------------------------------------------------------------------
      baz:
    -   qux: 43
    ?        ^^
    +   qux: 11
    ?        ^^
      foo:
        bar: 42
    """ % (
        str(a),
        str(b),
    )
    for line in dedent(expected).strip("\n").split("\n"):
        assert logged(line)


def test_config_tools_compare__missing_key(compare_assets, logged):
    d, a, b = compare_assets
    del d["baz"]
    with writable(b) as f:
        yaml.dump(d, f)
    # Note that a and b are swapped:
    assert not tools.compare(path1=b, format1=FORMAT.yaml, path2=a, format2=FORMAT.yaml)
    expected = """
    - %s
    + %s
    ---------------------------------------------------------------------
    ↓ ? = info | -/+ = line unique to - or + file | blank = matching line
    ---------------------------------------------------------------------
    + baz:
    +   qux: 43
      foo:
        bar: 42
    """ % (
        str(b),
        str(a),
    )
    for line in dedent(expected).strip("\n").split("\n"):
        assert logged(line)


def test_config_tools_compare__bad_format(logged):
    assert not tools.compare(
        path1=Path("/not/used"),
        format1="jpg",
        path2=Path("/not/used"),
        format2=FORMAT.yaml,
    )
    msg = "Formats do not match: jpg vs yaml"
    assert logged(msg)


@mark.parametrize(("configclass", "fmt"), [(INIConfig, FORMAT.ini), (NMLConfig, FORMAT.nml)])
def test_config_tools_compose__fmt_ini_nml_2x(configclass, fmt, logged, tmp_path):
    d = {"constants": {"pi": 3.142, "e": 2.718}, "trees": {"leaf": "elm", "needle": "spruce"}}
    u = {"trees": {"needle": "fir"}, "colors": {"red": "crimson", "green": "clover"}}
    suffix = f".{fmt}"
    dpath, upath = [(tmp_path / x).with_suffix(suffix) for x in ("d", "u")]
    configclass(d).dump(dpath)
    configclass(u).dump(upath)
    outpath = (tmp_path / "out").with_suffix(suffix)
    kwargs: dict = {"configs": [dpath, upath], "realize": False, "output_file": outpath}
    assert tools.compose(**kwargs) is True
    assert logged(f"Reading {dpath} as base '{fmt}' config")
    assert logged(f"Composing '{fmt}' config from {upath}")
    constants = {"pi": 3.142, "e": 2.718}
    expected = {
        "constants": constants,
        "trees": {"leaf": "elm", "needle": "fir"},
        "colors": {"red": "crimson", "green": "clover"},
    }
    if fmt == FORMAT.ini:
        # All values in INI configs are strings:
        expected["constants"] = {k: str(v) for k, v in constants.items()}
    assert configclass(outpath) == configclass(expected)


def test_config_tools_compose__fmt_sh_2x(logged, tmp_path):
    d = {"foo": 1, "bar": 2}
    u = {"foo": 3, "baz": 4}
    dpath, upath = [tmp_path / x for x in ("d.sh", "u.sh")]
    SHConfig(d).dump(dpath)
    SHConfig(u).dump(upath)
    outpath = tmp_path / "out.sh"
    kwargs: dict = {"configs": [dpath, upath], "realize": False, "output_file": outpath}
    assert tools.compose(**kwargs) is True
    assert logged(f"Reading {dpath} as base 'sh' config")
    assert logged(f"Composing 'sh' config from {upath}")
    assert SHConfig(outpath) == SHConfig({"foo": "3", "bar": "2", "baz": "4"})


@mark.parametrize("tofile", [False, True])
@mark.parametrize("suffix", ["", ".yaml", ".foo"])
def test_config_tools_compose__fmt_yaml_1x(compose_assets_yaml, logged, suffix, tmp_path, tofile):
    d1, _, d2, _, d3, _ = compose_assets_yaml
    dpath = (tmp_path / "d").with_suffix(suffix)
    for d in (d1, d2, d3):
        dpath.unlink(missing_ok=True)
        assert not dpath.exists()
        dpath.write_text(yaml.dump(d))
        kwargs: dict = {"configs": [dpath], "realize": False}
        if suffix and suffix != ".yaml":
            kwargs["input_format"] = FORMAT.yaml
        if tofile:
            outpath = (tmp_path / "out").with_suffix(suffix)
            kwargs["output_file"] = outpath
        assert tools.compose(**kwargs) is True
        assert logged(f"Reading {dpath} as base 'yaml' config")
        if tofile:
            assert YAMLConfig(outpath) == d
            outpath.unlink()


@mark.parametrize("tofile", [False, True])
@mark.parametrize("suffix", ["", ".yaml", ".foo"])
def test_config_tools_compose__fmt_yaml_2x(compose_assets_yaml, logged, suffix, tmp_path, tofile):
    d1, u1, d2, u2, d3, u3 = compose_assets_yaml
    dpath, upath = [(tmp_path / x).with_suffix(suffix) for x in ("d", "u")]
    for d, u in [(d1, u1), (d2, u2), (d3, u3)]:
        for path in [dpath, upath]:
            path.unlink(missing_ok=True)
            assert not path.exists()
        dpath.write_text(yaml.dump(d))
        upath.write_text(yaml.dump(u))
        kwargs: dict = {"configs": [dpath, upath], "realize": False}
        if suffix and suffix != ".yaml":
            kwargs["input_format"] = FORMAT.yaml
        if tofile:
            outpath = (tmp_path / "out").with_suffix(suffix)
            kwargs["output_file"] = outpath
        assert tools.compose(**kwargs) is True
        assert logged(f"Reading {dpath} as base 'yaml' config")
        assert logged(f"Composing 'yaml' config from {upath}")
        if tofile:
            expected = {
                str(u1): {"k10": "u10", "k11": "v11", "k12": "v12"},
                str(u2): {"k10": {"k21": "u21", "k22": "v22"}, "k11": "v11", "k12": "v12"},
                str(u3): {
                    "k10": {
                        "k21": {"k31": ["v310", "v311"], "k32": "v32", "k33": "v33"},
                        "k22": "v22",
                    },
                    "k11": "v11",
                },
            }
            assert YAMLConfig(outpath) == expected[str(u)]
            outpath.unlink()


@mark.parametrize("realize", [False, True])
def test_config_tools_compose__realize(realize, tmp_path):
    dyaml = """
    radius: !float '{{ 2.0 * pi * r }}'
    """
    dpath = tmp_path / "d.yaml"
    dpath.write_text(dedent(dyaml))
    uyaml = """
    pi: 3.142
    r: 1.0
    """
    upath = tmp_path / "u.yaml"
    upath.write_text(dedent(uyaml))
    outpath = tmp_path / "out.yaml"
    assert tools.compose(configs=[dpath, upath], realize=realize, output_file=outpath) is True
    radius = YAMLConfig(outpath)["radius"]
    assert (radius == 6.284) if realize else (radius.tagged_string == "!float '{{ 2.0 * pi * r }}'")


@mark.parametrize(
    ("cfgtype", "fmt"),
    [
        (FieldTableConfig, FORMAT.fieldtable),
        (INIConfig, FORMAT.ini),
        (NMLConfig, FORMAT.nml),
        (SHConfig, FORMAT.sh),
        (YAMLConfig, FORMAT.yaml),
    ],
)
def test_config_tools_config_tools_format_to_config(cfgtype, fmt):
    assert tools.format_to_config(fmt) is cfgtype


def test_config_tools_config_tools_format_to_config__fail():
    with raises(UWConfigError):
        tools.format_to_config("no-such-config-type")


def test_config_tools_realize__conversion_cfg_to_yaml(tmp_path):
    """
    Test that a .cfg file can be used to create a YAML object.
    """
    infile = fixture_path("srw_example_yaml.cfg")
    outfile = tmp_path / "test_ouput.yaml"
    tools.realize(
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
    assert outfile.read_text()[-1] == "\n"


def test_config_tools_realize__depth_mismatch_to_ini(realize_yaml_input):
    with raises(UWConfigError):
        tools.realize(
            input_config=realize_yaml_input,
            input_format=FORMAT.yaml,
            output_format=FORMAT.ini,
        )


def test_config_tools_realize__depth_mismatch_to_sh(realize_yaml_input):
    with raises(UWConfigError):
        tools.realize(
            input_config=realize_yaml_input,
            input_format=FORMAT.yaml,
            output_format=FORMAT.sh,
        )


def test_config_tools_realize__double_tag_flat(tmp_path):
    config = """
    a: 1
    b: 2
    foo: !int "{{ a + b }}"
    bar: !int "{{ foo }}"
    """
    expected = """
    a: 1
    b: 2
    foo: 3
    bar: 3
    """
    help_realize_double_tag(config, expected, tmp_path)


def test_config_tools_realize__double_tag_nest(tmp_path):
    config = """
    a: 1.0
    b: 2.0
    qux:
      foo: !float "{{ a + b }}"
      bar: !float "{{ foo }}"
    """
    expected = """
    a: 1.0
    b: 2.0
    qux:
      foo: 3.0
      bar: 3.0
    """
    help_realize_double_tag(config, expected, tmp_path)


def test_config_tools_realize__double_tag_nest_forward_reference(tmp_path):
    config = """
    a: true
    b: false
    bar: !bool "{{ qux.foo }}"
    qux:
      foo: !bool "{{ a or b }}"
    """
    expected = """
    a: true
    b: false
    bar: true
    qux:
      foo: true
    """
    help_realize_double_tag(config, expected, tmp_path)


def test_config_tools_realize__dry_run(logged):
    """
    Test that providing a YAML base file with a dry-run flag will print an YAML config file.
    """
    infile = fixture_path("fruit_config.yaml")
    yaml_config = YAMLConfig(infile)
    yaml_config.dereference()
    tools.realize(
        input_config=infile,
        input_format=FORMAT.yaml,
        output_format=FORMAT.yaml,
        dry_run=True,
    )
    assert logged(str(yaml_config), multiline=True)


def test_config_tools_realize__field_table(tmp_path):
    """
    Test reading a YAML config object and generating a field file table.
    """
    infile = fixture_path("FV3_GFS_v16.yaml")
    outfile = tmp_path / "field_table_from_yaml.FV3_GFS"
    tools.realize(
        input_config=infile,
        input_format=FORMAT.yaml,
        output_file=outfile,
        output_format=FORMAT.fieldtable,
    )
    f1_lines = fixture_path("field_table.FV3_GFS_v16").read_text().split("\n")
    f2_lines = outfile.read_text().split("\n")
    reflist = [line.rstrip("\n").strip().replace("'", "") for line in f1_lines]
    outlist = [line.rstrip("\n").strip().replace("'", "") for line in f2_lines]
    lines = zip(outlist, reflist)
    for line1, line2 in lines:
        assert line1 in line2


def test_config_tools_realize__fmt2fmt_nml2nml(tmp_path):
    """
    Test that providing a namelist base input file and a config file will create and update namelist
    config file.
    """
    help_realize_fmt2fmt("simple.nml", FORMAT.nml, "simple2.nml", FORMAT.nml, tmp_path)


def test_config_tools_realize__fmt2fmt_ini2ini(tmp_path):
    """
    Test that providing an INI base input file and an INI config file will create and update INI
    config file.
    """
    help_realize_fmt2fmt("simple.ini", FORMAT.ini, "simple2.ini", FORMAT.ini, tmp_path)


def test_config_tools_realize__fmt2fmt_yaml2yaml(tmp_path):
    """
    Test that providing a YAML base input file and a YAML config file will create and update YAML
    config file.
    """
    help_realize_fmt2fmt(
        "fruit_config.yaml", FORMAT.yaml, "fruit_config_similar.yaml", FORMAT.yaml, tmp_path
    )


def test_config_tools_realize__incompatible_file_type():
    """
    Test that providing an incompatible file type for input base file will return print statement.
    """
    with raises(UWError):
        tools.realize(
            input_config=fixture_path("model_configure.sample"),
            input_format="sample",
            output_format=FORMAT.yaml,
        )


def test_config_tools_realize__output_file_format(tmp_path):
    """
    Test that output_format overrides bad output_file extension.
    """
    infile = fixture_path("simple.nml")
    outfile = tmp_path / "test_ouput.cfg"
    tools.realize(
        input_config=infile,
        output_file=outfile,
        output_format=FORMAT.nml,
    )
    assert compare_files(outfile, infile)


def test_config_tools_realize__remove_nml_to_nml(tmp_path):
    input_config = NMLConfig({"constants": {"pi": 3.141, "e": 2.718}})
    s = """
    constants:
      e: !remove
    """
    update_config = tmp_path / "update.yaml"
    update_config.write_text(dedent(s).strip())
    output_file = tmp_path / "config.nml"
    assert not output_file.is_file()
    tools.realize(
        input_config=input_config,
        update_config=update_config,
        output_file=output_file,
    )
    assert f90nml.read(output_file) == {"constants": {"pi": 3.141}}


def test_config_tools_realize__remove_yaml_to_yaml_scalar(tmp_path):
    input_config = YAMLConfig({"a": {"b": {"c": 11, "d": 22, "e": 33}}})
    s = """
    a:
      b:
        d: !remove
    """
    update_config = tmp_path / "update.yaml"
    update_config.write_text(dedent(s).strip())
    assert tools.realize(
        input_config=input_config,
        update_config=update_config,
        output_format=FORMAT.yaml,
    ) == {"a": {"b": {"c": 11, "e": 33}}}


def test_config_tools_realize__remove_yaml_to_yaml_subtree(tmp_path):
    input_config = YAMLConfig(yaml.safe_load("a: {b: {c: 11, d: 22, e: 33}}"))
    s = """
    a:
      b: !remove
    """
    update_config = tmp_path / "update.yaml"
    update_config.write_text(dedent(s).strip())
    assert tools.realize(
        input_config=input_config,
        update_config=update_config,
        output_format=FORMAT.yaml,
    ) == {"a": {}}


def test_config_tools_realize__scalar_value(capsys):
    stdinproxy.cache_clear()
    tools.realize(
        input_config=YAMLConfig(config={"foo": {"bar": "baz"}}),
        output_format="yaml",
        key_path=["foo", "bar"],
    )
    assert capsys.readouterr().out.strip() == "baz"


def test_config_tools_realize__simple_ini(tmp_path):
    """
    Test that providing an INI file with necessary settings will create an INI config file.
    """
    help_realize_simple("simple.ini", FORMAT.ini, tmp_path)


def test_config_tools_realize__simple_namelist(tmp_path):
    """
    Test that providing a namelist file with necessary settings will create a namelist config file.
    """
    help_realize_simple("simple.nml", FORMAT.nml, tmp_path)


def test_config_tools_realize__simple_sh(tmp_path):
    """
    Test that providing an sh file with necessary settings will create an sh config file.
    """
    help_realize_simple("simple.sh", FORMAT.sh, tmp_path)


def test_config_tools_realize__simple_yaml(tmp_path):
    """
    Test that providing a YAML base file with necessary settings will create a YAML config file.
    """
    help_realize_simple("simple2.yaml", FORMAT.yaml, tmp_path)


def test_config_tools_realize__single_dereference(capsys, tmp_path):
    input_config = tmp_path / "a.yaml"
    update_config = tmp_path / "b.yaml"
    with writable(input_config) as f:
        yaml.dump({"1": "a", "2": "{{ deref }}", "3": "{{ temporalis }}"}, f)
    with writable(update_config) as f:
        yaml.dump({"2": "b", "temporalis": "c", "deref": "d"}, f)
    tools.realize(
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


def test_config_tools_realize__total_fail():
    with raises(UWConfigError) as e:
        tools.realize(
            input_config=YAMLConfig({"foo": "{{ bar }}"}), output_format=FORMAT.yaml, total=True
        )
    assert str(e.value) == "Config could not be totally realized"


def test_config_tools_realize__update_bad_format_defaults_to_yaml(capsys, tmp_path):
    input_config = tmp_path / "a.yaml"
    update_config = tmp_path / "b.clj"
    with writable(input_config) as f:
        yaml.dump({"1": "a", "2": "{{ deref }}", "3": "{{ temporalis }}", "deref": "b"}, f)
    with writable(update_config) as f:
        yaml.dump({"2": "b", "temporalis": "c"}, f)
    tools.realize(
        input_config=input_config,
        update_config=update_config,
        output_format=FORMAT.yaml,
    )
    expected = """
    '1': a
    '2': b
    '3': c
    deref: b
    temporalis: c
    """
    assert capsys.readouterr().out.strip() == dedent(expected).strip()


def test_config_tools_realize__update_none(capsys, tmp_path):
    path = tmp_path / "a.yaml"
    with writable(path) as f:
        yaml.dump({"1": "a", "2": "{{ deref }}", "3": "{{ temporalis }}", "deref": "b"}, f)
    tools.realize(
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


def test_config_tools_realize__values_needed_ini(logged):
    """
    Test that the values_needed flag logs keys completed and keys containing unrendered Jinja2
    variables/expressions.
    """
    tools.realize(
        input_config=fixture_path("simple3.ini"),
        input_format=FORMAT.ini,
        output_format=FORMAT.ini,
        values_needed=True,
    )
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
    assert logged(dedent(expected), multiline=True)


def test_config_tools_realize__values_needed_yaml(logged):
    """
    Test that the values_needed flag logs keys completed and keys containing unrendered Jinja2
    variables/expressions.
    """
    tools.realize(
        input_config=fixture_path("srw_example.yaml"),
        input_format=FORMAT.yaml,
        output_format=FORMAT.yaml,
        values_needed=True,
    )
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
    """  # noqa: E501
    assert logged(dedent(expected), multiline=True)


@mark.parametrize(
    ("fmt", "obj"),
    [
        (FORMAT.fieldtable, 42),
        (FORMAT.ini, {1: 11}),
        (FORMAT.ini, {1: {2: {3: 33}}}),
        (FORMAT.nml, {1: 11}),
        (FORMAT.sh, 42),
        (FORMAT.sh, {1: {2: 22}}),
    ],
)
def test_config_tools_validate_depth__fail(fmt, obj):
    with raises(UWConfigError) as e:
        tools.validate_depth(config_obj=obj, target_format=fmt)
    assert str(e.value) == "Cannot treat depth-%s config as '%s'" % (tools.depth(obj), fmt)


@mark.parametrize(
    ("fmt", "obj"),
    [
        (FORMAT.ini, {1: {2: 22}}),
        (FORMAT.nml, {1: {2: 22}}),
        (FORMAT.nml, {1: {2: {3: 33}}}),
        (FORMAT.sh, {1: 11}),
    ],
)
def test_config_tools_validate_depth__pass(fmt, obj):
    tools.validate_depth(config_obj=obj, target_format=fmt)


def test_config_tools_walk_key_path():
    expected = ({"c": "cherry"}, "a.b")
    assert tools.walk_key_path({"a": {"b": {"c": "cherry"}}}, ["a", "b"]) == expected


def test_config_tools_walk_key_path__fail_bad_key_path():
    with raises(UWError) as e:
        tools.walk_key_path({"a": {"b": {"c": "cherry"}}}, ["a", "x"])
    assert str(e.value) == "Bad config path: a.x"


def test_config_tools_walk_key_path__fail_bad_leaf_value():
    with raises(UWError) as e:
        tools.walk_key_path({"a": {"b": {"c": "cherry"}}}, ["a", "b", "c"])
    assert str(e.value) == "Value at a.b.c must be a dictionary"


def test_config_tools__ensure_format__no_path_no_format(logged):
    assert tools._ensure_format(desc="foo") == FORMAT.yaml
    assert logged(f"Treating foo config as '{FORMAT.yaml}'")


def test_config_tools__ensure_format__config_obj():
    config = NMLConfig({"nl": {"n": 42}})
    assert tools._ensure_format(desc="foo", config=config) == FORMAT.nml


def test_config_tools__ensure_format__dict_explicit():
    assert tools._ensure_format(desc="foo", fmt=FORMAT.yaml, config={}) == FORMAT.yaml


def test_config_tools__ensure_format__dict_implicit():
    assert tools._ensure_format(desc="foo", config={}) == FORMAT.yaml


def test_config_tools__ensure_format__deduced():
    assert tools._ensure_format(desc="foo", config=Path("/some/config.nml")) == FORMAT.nml


def test_config_tools__ensure_format__explicitly_specified_no_path():
    assert tools._ensure_format(desc="foo", fmt=FORMAT.ini) == FORMAT.ini


def test_config_tools__ensure_format__explicitly_specified_with_path():
    assert (
        tools._ensure_format(desc="foo", fmt=FORMAT.ini, config=Path("/some/config.yaml"))
        == FORMAT.ini
    )


def test_config_tools__realize_input_setup__ini_cfgobj():
    data = {"section": {"foo": "bar"}}
    cfgobj = INIConfig(config=data)
    input_obj = tools._realize_input_setup(input_config=cfgobj)
    assert input_obj.data == data


def test_config_tools__realize_input_setup__ini_file(tmp_path):
    data = """
    [section]
    foo = bar
    """
    path = tmp_path / "config.ini"
    path.write_text(dedent(data).strip())
    input_obj = tools._realize_input_setup(input_config=path)
    assert input_obj.data == {"section": {"foo": "bar"}}


def test_config_tools__realize_input_setup__ini_stdin(logged):
    data = """
    [section]
    foo = bar
    baz = 42
    """
    stdinproxy.cache_clear()
    with StringIO() as sio:
        print(dedent(data).strip(), file=sio)
        sio.seek(0)
        with patch.object(sys, "stdin", new=sio):
            input_obj = tools._realize_input_setup(input_format=FORMAT.ini)
    assert input_obj.data == {"section": {"foo": "bar", "baz": "42"}}  # note: 42 is str, not int
    assert logged("Reading input from stdin")


def test_config_tools__realize_input_setup__nml_cfgobj():
    data = {"nl": {"pi": 3.14}}
    cfgobj = NMLConfig(config=data)
    input_obj = tools._realize_input_setup(input_config=cfgobj)
    assert input_obj.data == data


def test_config_tools__realize_input_setup__nml_file(tmp_path):
    data = """
    &nl
      pi = 3.14
    /
    """
    path = tmp_path / "config.nml"
    path.write_text(dedent(data).strip())
    input_obj = tools._realize_input_setup(input_config=path)
    assert input_obj["nl"]["pi"] == 3.14


def test_config_tools__realize_input_setup__nml_stdin(logged):
    data = """
    &nl
      pi = 3.14
    /
    """
    stdinproxy.cache_clear()
    with StringIO() as sio:
        print(dedent(data).strip(), file=sio)
        sio.seek(0)
        with patch.object(sys, "stdin", new=sio):
            input_obj = tools._realize_input_setup(input_format=FORMAT.nml)
    assert input_obj["nl"]["pi"] == 3.14
    assert logged("Reading input from stdin")


def test_config_tools__realize_input_setup__sh_cfgobj():
    data = {"foo": "bar"}
    cfgobj = SHConfig(config=data)
    input_obj = tools._realize_input_setup(input_config=cfgobj)
    assert input_obj.data == data


def test_config_tools__realize_input_setup__sh_file(tmp_path):
    data = """
    foo=bar
    """
    path = tmp_path / "config.sh"
    path.write_text(dedent(data).strip())
    input_obj = tools._realize_input_setup(input_config=path)
    assert input_obj.data == {"foo": "bar"}


def test_config_tools__realize_input_setup__sh_stdin(logged):
    data = """
    foo=bar
    """
    stdinproxy.cache_clear()
    with StringIO() as sio:
        print(dedent(data).strip(), file=sio)
        sio.seek(0)
        with patch.object(sys, "stdin", new=sio):
            input_obj = tools._realize_input_setup(input_format=FORMAT.sh)
    assert input_obj.data == {"foo": "bar"}
    assert logged("Reading input from stdin")


def test_config_tools__realize_input_setup__yaml_cfgobj():
    data = {"foo": "bar"}
    cfgobj = YAMLConfig(config=data)
    input_obj = tools._realize_input_setup(input_config=cfgobj)
    assert input_obj.data == data


def test_config_tools__realize_input_setup__yaml_file(tmp_path):
    data = """
    foo: bar
    """
    path = tmp_path / "config.yaml"
    path.write_text(dedent(data).strip())
    input_obj = tools._realize_input_setup(input_config=path)
    assert input_obj.data == {"foo": "bar"}


def test_config_tools__realize_input_setup__yaml_stdin(logged):
    data = """
    foo: bar
    """
    stdinproxy.cache_clear()
    with StringIO() as sio:
        print(dedent(data).strip(), file=sio)
        sio.seek(0)
        with patch.object(sys, "stdin", new=sio):
            input_obj = tools._realize_input_setup(input_format=FORMAT.yaml)
    assert input_obj.data == {"foo": "bar"}
    assert logged("Reading input from stdin")


def test_config_tools__realize_output_setup(logged, tmp_path):
    input_obj = YAMLConfig({"a": {"b": {"foo": "bar"}}})
    output_file = tmp_path / "output.yaml"
    assert tools._realize_output_setup(
        input_obj=input_obj, output_file=output_file, key_path=["a", "b"]
    ) == ({"foo": "bar"}, FORMAT.yaml)
    assert logged(f"Writing output to {output_file}")


def test_config_tools__realize_update__cfgobj(realize_testobj):
    assert realize_testobj[1][2][3] == 42
    update_config = YAMLConfig(config={1: {2: {3: 43}}})
    o = tools._realize_update(input_obj=realize_testobj, update_config=update_config)
    assert o[1][2][3] == 43


def test_config_tools__realize_update__stdin(logged, realize_testobj):
    stdinproxy.cache_clear()
    assert realize_testobj[1][2][3] == 42
    with StringIO() as sio:
        print("{1: {2: {3: 43}}}", file=sio)
        sio.seek(0)
        with patch.object(sys, "stdin", new=sio):
            o = tools._realize_update(input_obj=realize_testobj, update_format=FORMAT.yaml)
    assert o[1][2][3] == 43
    assert logged("Reading update from stdin")


def test_config_tools__realize_update__noop(realize_testobj):
    assert tools._realize_update(input_obj=realize_testobj) == realize_testobj


def test_config_tools__realize_update__file(realize_testobj, tmp_path):
    assert realize_testobj[1][2][3] == 42
    values = {1: {2: {3: 43}}}
    update_config = tmp_path / "config.yaml"
    update_config.write_text(yaml.dump(values))
    o = tools._realize_update(input_obj=realize_testobj, update_config=update_config)
    assert o[1][2][3] == 43


def test_config_tools__realize_values_needed(logged, tmp_path):
    path = tmp_path / "a.yaml"
    with writable(path) as f:
        yaml.dump({1: "complete", 2: "{{ jinja2 }}", 3: ""}, f)
    c = YAMLConfig(config=path)
    tools._realize_values_needed(input_obj=c)
    assert logged("Keys that are complete:\n  1", multiline=True)
    assert logged("Keys with unrendered Jinja2 variables/expressions:\n  2", multiline=True)


def test_config_tools__realize_values_needed__negative_results(logged, tmp_path):
    path = tmp_path / "a.yaml"
    with writable(path) as f:
        yaml.dump({}, f)
    c = YAMLConfig(config=path)
    tools._realize_values_needed(input_obj=c)
    assert logged("No keys are complete.")
    assert logged("No keys have unrendered Jinja2 variables/expressions.")


@mark.parametrize("input_fmt", FORMAT.extensions())
@mark.parametrize("other_fmt", FORMAT.extensions())
def test_config_tools__validate_format(input_fmt, other_fmt):
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
