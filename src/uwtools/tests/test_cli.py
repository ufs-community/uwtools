import re
import sys
from argparse import ArgumentParser as Parser
from argparse import _SubParsersAction
from datetime import timedelta
from pathlib import Path
from textwrap import dedent
from unittest.mock import Mock, patch

from pytest import fixture, mark, raises

import uwtools.api
import uwtools.api.config
import uwtools.api.ecflow
import uwtools.api.rocoto
import uwtools.api.template
from uwtools import cli
from uwtools.cli import STR
from uwtools.exceptions import UWConfigRealizeError, UWError, UWTemplateRenderError
from uwtools.strings import FORMAT

# Helpers


def actions(parser: Parser) -> list[str]:
    # Return actions (named subparsers) belonging to the given parser.
    actions = [x for x in parser._actions if isinstance(x, _SubParsersAction)]
    return list(actions[0].choices.keys())


# Fixtures


@fixture
def args_config_realize(utc):
    return {
        STR.input_file: "in",
        STR.input_format: "yaml",
        STR.update_file: "update",
        STR.update_format: "yaml",
        STR.output_file: "out",
        STR.output_format: "yaml",
        STR.key_path: "foo.bar",
        STR.cycle: utc(2025, 11, 12, 6),
        STR.leadtime: timedelta(hours=6),
        STR.values_needed: False,
        STR.total: False,
        STR.dry_run: False,
    }


@fixture
def args_dispatch_fs(utc):
    return {
        "target_dir": "/target/dir",
        "config_file": "/config/file",
        "cycle": utc(),
        "leadtime": timedelta(hours=6),
        "key_path": ["a", "b"],
        "dry_run": False,
        "threads": 3,
        "report": True,
        "stdin_ok": True,
    }


@fixture
def subparsers():
    # Create and return a subparsers test object.
    return Parser().add_subparsers()


# Test functions


def test_cli__abort(capsys):
    msg = "Aborting..."
    with raises(SystemExit) as e:
        cli._abort(msg)
    assert e.value.code == 1
    assert msg in capsys.readouterr().err


def test_cli__add_subparser_config(subparsers):
    cli._add_subparser_config(subparsers)
    assert actions(subparsers.choices[STR.config]) == [
        STR.compare,
        STR.compose,
        STR.realize,
        STR.validate,
    ]


def test_cli__add_subparser_config_compare(subparsers):
    cli._add_subparser_config_compare(subparsers)
    assert subparsers.choices[STR.compare]


def test_cli__add_subparser_config_compose(subparsers):
    cli._add_subparser_config_compose(subparsers)
    assert subparsers.choices[STR.compose]


def test_cli__add_subparser_config_realize(subparsers):
    cli._add_subparser_config_realize(subparsers)
    assert subparsers.choices[STR.realize]


def test_cli__add_subparser_config_validate(subparsers):
    cli._add_subparser_config_validate(subparsers)
    assert subparsers.choices[STR.validate]


def test_cli__add_subparser_ecflow(subparsers):
    cli._add_subparser_ecflow(subparsers)
    assert actions(subparsers.choices[STR.ecflow]) == [STR.realize, STR.validate]


def test_cli__add_subparser_ecflow_realize(subparsers):
    cli._add_subparser_ecflow_realize(subparsers)
    assert subparsers.choices[STR.realize]


def test_cli__add_subparser_ecflow_validate(subparsers):
    cli._add_subparser_ecflow_validate(subparsers)
    assert subparsers.choices[STR.validate]


def test_cli__add_subparser_file(subparsers):
    cli._add_subparser_fs(subparsers)
    assert actions(subparsers.choices[STR.fs]) == [STR.copy, STR.hardlink, STR.link, STR.makedirs]


def test_cli__add_subparser_file_copy(subparsers):
    cli._add_subparser_fs_copy(subparsers)
    assert subparsers.choices[STR.copy]


def test_cli__add_subparser_file_link(subparsers):
    cli._add_subparser_fs_link(subparsers)
    assert subparsers.choices[STR.link]


def test_cli__add_subparser_for_driver(subparsers):
    name = "adriver"
    adriver = Mock()
    adriver.tasks.return_value = {"task1": "task1 description", "task2": "task2 description"}
    with patch.object(cli, "import_module", return_value=adriver):
        cli._add_subparser_for_driver(name, subparsers, with_cycle=True)
    assert actions(subparsers.choices[name]) == ["task1", "task2"]


def test_cli__add_subparser_for_driver_task(subparsers):
    assert not subparsers.choices
    cli._add_subparser_for_driver_task(subparsers, "task1", "task1 description", with_cycle=True)
    assert subparsers.choices["task1"]


def test_cli__add_subparser_rocoto(subparsers):
    cli._add_subparser_rocoto(subparsers)
    assert subparsers.choices[STR.rocoto]


def test_cli__add_subparser_rocoto_realize(subparsers):
    cli._add_subparser_rocoto_realize(subparsers)
    assert subparsers.choices[STR.realize]


def test_cli__add_subparser_rocoto_validate_xml(subparsers):
    cli._add_subparser_rocoto_validate_xml(subparsers)
    assert subparsers.choices[STR.validatexml]


def test_cli__add_subparser_template(subparsers):
    cli._add_subparser_template(subparsers)
    assert actions(subparsers.choices[STR.template]) == [STR.render, STR.translate]


def test_cli__add_subparser_template_render(subparsers):
    cli._add_subparser_template_render(subparsers)
    assert subparsers.choices[STR.render]


def test_cli__add_subparser_template_translate(subparsers):
    cli._add_subparser_template_translate(subparsers)
    assert subparsers.choices[STR.translate]


def test_cli__dispatch_execute(utc):
    cycle = utc()
    args: dict = {
        "module": "testdriver",
        "classname": "TestDriver",
        "schema_file": "/path/to/testdriver.jsonschema",
        "batch": True,
        "config_file": "/path/to/config",
        "cycle": cycle,
        "leadtime": None,
        "dry_run": False,
        "graph_file": None,
        "key_path": ["foo", "bar"],
        "task": "forty_two",
        "stdin_ok": True,
    }
    with patch.object(cli.uwtools.api.execute, "execute") as execute:
        cli._dispatch_execute(args=args)
        execute.assert_called_once_with(
            classname="TestDriver",
            module="testdriver",
            task="forty_two",
            schema_file="/path/to/testdriver.jsonschema",
            key_path=["foo", "bar"],
            dry_run=False,
            config="/path/to/config",
            graph_file=None,
            cycle=cycle,
            leadtime=None,
            batch=True,
            stdin_ok=True,
        )


@mark.parametrize(
    ("file_arg", "format_arg"),
    [
        (STR.path1, STR.format1),
        (STR.path2, STR.format2),
        (STR.input_file, STR.input_format),
        (STR.output_file, STR.output_format),
        (STR.values_file, STR.values_format),
    ],
)
def test_cli__check_file_vs_format_fail(file_arg, format_arg):
    # When reading/writing from/to stdin/stdout, the data format is assumed to be YAML when not
    # otherwise specified.
    args = {file_arg: None, format_arg: None}
    actual = cli._check_file_vs_format(file_arg=file_arg, format_arg=format_arg, args=args)
    expected = {**args, format_arg: FORMAT.yaml}
    assert actual == expected


def test_cli__check_file_vs_format_pass_explicit():
    # Accept explicitly-specified format, whatever it is.
    fmt = "jpg"
    args = {STR.input_file: "/path/to/input.txt", STR.input_format: fmt}
    args = cli._check_file_vs_format(
        file_arg=STR.input_file,
        format_arg=STR.input_format,
        args=args,
    )
    assert args[STR.input_format] == fmt


@mark.parametrize("fmt", FORMAT.formats())
def test_cli__check_file_vs_format_pass_implicit(fmt):
    # The format is correctly deduced for a file with a known extension.
    args = {STR.input_file: f"/path/to/input.{fmt}", STR.input_format: None}
    args = cli._check_file_vs_format(
        file_arg=STR.input_file, format_arg=STR.input_format, args=args
    )
    assert args[STR.input_format] == vars(FORMAT)[fmt]


def test_cli__check_template_render_vals_args_implicit_fail():
    # The values-file format cannot be deduced from the filename.
    args = {STR.values_file: "a.jpg"}
    expected = {"values_file": "a.jpg", "values_format": FORMAT.yaml}
    assert cli._check_template_render_vals_args(args) == expected


def test_cli__check_template_render_vals_args_implicit_pass():
    # The values-file format is deduced from the filename.
    args = {STR.values_file: "a.yaml"}
    checked = cli._check_template_render_vals_args(args)
    assert checked[STR.values_format] == FORMAT.yaml


def test_cli__check_template_render_vals_args_noop_no_valsfile():
    # No values file is provided, so format is irrelevant.
    args = {STR.values_file: None}
    assert cli._check_template_render_vals_args(args) == args


def test_cli__check_template_render_vals_args_noop_explicit_valsfmt():
    # An explicit values format is honored, valid or not.
    args = {STR.values_file: "a.txt", STR.values_format: "jpg"}
    assert cli._check_template_render_vals_args(args) == args


@mark.parametrize(
    ("expected", "fmt", "fn"),
    [
        (FORMAT.yaml, None, "a.yaml"),  # yaml correctly deduced
        (FORMAT.yaml, "yaml", "a.nml"),  # explicit yaml overrides deduced nml
        (FORMAT.yaml, "yaml", "a.txt"),  # explicit yaml overrides unrecognized txt
        (FORMAT.nml, None, "a.nml"),  # nml correctly deduced
        (FORMAT.ini, None, "a.ini"),  # ini correctly deduced
        (FORMAT.sh, None, "a.sh"),  # sh correctly deduced
    ],
)
def test_cli__check_update(expected, fmt, fn):
    args = {STR.update_file: fn, STR.update_format: fmt}
    assert cli._check_update(args) == {STR.update_file: fn, STR.update_format: expected}


def test_cli__check_verbosity_fail(capsys):
    args = {STR.quiet: True, STR.verbose: True}
    with raises(SystemExit):
        cli._check_verbosity(args)
    assert "--quiet may not be used with --verbose" in capsys.readouterr().err


@mark.parametrize("flags", [[STR.quiet], [STR.verbose]])
def test_cli__check_verbosity_ok(flags):
    args = dict.fromkeys(flags, True)
    assert cli._check_verbosity(args) == args


def test_cli__dict_from_key_eq_val_strings():
    assert not cli._dict_from_key_eq_val_strings([])
    assert cli._dict_from_key_eq_val_strings(["a=1", "b=2"]) == {"a": "1", "b": "2"}


@mark.parametrize(
    "params",
    [
        (STR.compare, "_dispatch_config_compare"),
        (STR.compose, "_dispatch_config_compose"),
        (STR.realize, "_dispatch_config_realize"),
        (STR.validate, "_dispatch_config_validate"),
    ],
)
def test_cli__dispatch_config(params):
    action, funcname = params
    args = {STR.action: action}
    with patch.object(cli, funcname) as func:
        cli._dispatch_config(args)
    func.assert_called_once_with(args)


def test_cli__dispatch_config_compare():
    args = {STR.path1: 1, STR.format1: 2, STR.path2: 3, STR.format2: 4}
    with patch.object(cli.uwtools.api.config, "compare") as compare:
        cli._dispatch_config_compare(args)
    compare.assert_called_once_with(
        path1=args[STR.path1],
        format1=args[STR.format1],
        path2=args[STR.path2],
        format2=args[STR.format2],
    )


def test_cli__dispatch_config_compose(utc):
    configs = ["/path/to/a", "/path/to/b"]
    outfile = "/path/to/output"
    cycle = utc(2025, 11, 12, 6)
    leadtime = timedelta(hours=6)
    args = {
        STR.configs: configs,
        STR.realize: True,
        STR.output_file: outfile,
        STR.input_format: FORMAT.yaml,
        STR.output_format: FORMAT.yaml,
        STR.cycle: cycle,
        STR.leadtime: leadtime,
    }
    with patch.object(cli.uwtools.api.config, "compose") as compose:
        cli._dispatch_config_compose(args)
    compose.assert_called_once_with(
        configs=configs,
        realize=True,
        output_file=outfile,
        input_format=FORMAT.yaml,
        output_format=FORMAT.yaml,
        cycle=cycle,
        leadtime=leadtime,
    )


def test_cli__dispatch_config_realize(args_config_realize, utc):
    with patch.object(cli.uwtools.api.config, "realize") as realize:
        cli._dispatch_config_realize(args_config_realize)
    realize.assert_called_once_with(
        input_config="in",
        input_format="yaml",
        update_config="update",
        update_format="yaml",
        output_file="out",
        output_format="yaml",
        key_path="foo.bar",
        cycle=utc(2025, 11, 12, 6),
        leadtime=timedelta(hours=6),
        values_needed=False,
        total=False,
        dry_run=False,
        stdin_ok=True,
    )


@mark.parametrize("values_needed_requested", [True, False])
def test_cli__dispatch_config_realize_fail(args_config_realize, caplog, values_needed_requested):
    args_config_realize[STR.values_needed] = values_needed_requested
    with patch.object(cli.uwtools.api.config, "realize", side_effect=UWConfigRealizeError):
        assert cli._dispatch_config_realize(args_config_realize) is False
    assert "Config could not be realized." in caplog.text
    present = f"Try with {cli._switch(STR.values_needed)} for details." in caplog.text
    assert not present if values_needed_requested else present


def test_cli__dispatch_config_validate_config_obj():
    _dispatch_config_validate_args = {
        STR.schema_file: Path("/path/to/a.jsonschema"),
        STR.input_file: Path("/path/to/config.yaml"),
    }
    with patch.object(uwtools.api.config, "_validate_external") as _validate_external:
        cli._dispatch_config_validate(_dispatch_config_validate_args)
    _validate_external_args = {
        STR.schema_file: _dispatch_config_validate_args[STR.schema_file],
        "config_data": None,
        "config_path": _dispatch_config_validate_args[STR.input_file],
    }
    _validate_external.assert_called_once_with(**_validate_external_args, desc="config")


@mark.parametrize(
    ("action", "funcname"),
    [
        (STR.copy, "_dispatch_fs_copy"),
        (STR.hardlink, "_dispatch_fs_hardlink"),
        (STR.link, "_dispatch_fs_link"),
        (STR.makedirs, "_dispatch_fs_makedirs"),
    ],
)
def test_cli__dispatch_fs(action, funcname):
    args = {STR.action: action}
    with patch.object(cli, funcname) as func:
        cli._dispatch_fs(args)
    func.assert_called_once_with(args)


@mark.parametrize("action", ["copy", "hardlink", "link", "makedirs"])
def test_cli__dispatch_fs_action(action, args_dispatch_fs):
    api_fn = action
    args_actual = args_dispatch_fs
    args_expected = {
        "target_dir": args_actual["target_dir"],
        "config": args_actual["config_file"],
        "cycle": args_actual["cycle"],
        "leadtime": args_actual["leadtime"],
        "key_path": args_actual["key_path"],
        "dry_run": args_actual["dry_run"],
        "threads": args_actual["threads"],
        "stdin_ok": args_actual["stdin_ok"],
    }
    if action == "hardlink":
        api_fn = "link"
        extra = {"hardlink": True, "fallback": None}
        args_actual = {**args_actual, **extra}
        args_expected = {**args_expected, **extra}
    with (
        patch.object(cli.uwtools.api.fs, api_fn) as a,
        patch.object(cli, "_dispatch_fs_report") as _dispatch_fs_report,
    ):
        a.return_value = {STR.ready: ["/present"], STR.notready: ["/missing"]}
        getattr(cli, f"_dispatch_fs_{action}")(args_actual)
    a.assert_called_once_with(**args_expected)
    _dispatch_fs_report.assert_called_once_with(
        report={STR.ready: ["/present"], STR.notready: ["/missing"]}
    )


def test_cli__dispatch_fs_report_no(capsys):
    report = None
    cli._dispatch_fs_report(report=report)
    assert capsys.readouterr().out.strip() == ""


def test_cli__dispatch_fs_report_yes(capsys):
    report = {STR.ready: ["/present"], STR.notready: ["/missing"]}
    cli._dispatch_fs_report(report=report)
    expected = """
    {
      "notready": [
        "/missing"
      ],
      "ready": [
        "/present"
      ]
    }
    """
    assert capsys.readouterr().out.strip() == dedent(expected).strip()


@mark.parametrize(
    "params",
    [
        (STR.realize, "_dispatch_ecflow_realize"),
        (STR.validate, "_dispatch_ecflow_validate"),
    ],
)
def test_cli__dispatch_ecflow(params):
    action, funcname = params
    args = {STR.action: action}
    with patch.object(cli, funcname) as func:
        cli._dispatch_ecflow(args)
    func.assert_called_once_with(args)


def test_cli__dispatch_ecflow_realize():
    args = {STR.config_file: Path("/path/to/config.yaml"), STR.output_dir: Path("/path/to/output")}
    with patch.object(uwtools.api.ecflow, "realize") as realize:
        cli._dispatch_ecflow_realize(args)
    realize.assert_called_once_with(
        config=args[STR.config_file],
        output_path=args[STR.output_dir],
        scripts_path=args[STR.output_dir],
        stdin_ok=True,
    )


def test_cli__dispatch_ecflow_validate():
    args = {STR.config_file: Path("/path/to/config.yaml")}
    with patch.object(uwtools.api.ecflow, "validate") as validate:
        cli._dispatch_ecflow_validate(args)
    validate.assert_called_once_with(
        config=args[STR.config_file],
        stdin_ok=True,
    )


def test_cli__dispatch_ecflow_realize_no_optional():
    args = {STR.config_file: None, STR.output_dir: None}
    with patch.object(uwtools.api.ecflow, "realize") as realize:
        cli._dispatch_ecflow_realize(args)
    realize.assert_called_once_with(
        config=None,
        output_path=None,
        scripts_path=None,
        stdin_ok=True,
    )


def test_cli__dispatch_ecflow_validate_invalid():
    args = {STR.config_file: Path("/path/to/config.yaml")}
    with patch.object(uwtools.api.ecflow, "validate", return_value=False):
        assert cli._dispatch_ecflow_validate(args) is False


def test_cli__dispatch_ecflow_validate_no_optional():
    args = {STR.config_file: None}
    with patch.object(uwtools.api.ecflow, "validate") as validate:
        cli._dispatch_ecflow_validate(args)
    validate.assert_called_once_with(
        config=None,
        stdin_ok=True,
    )


@mark.parametrize(
    "params",
    [
        (STR.realize, "_dispatch_rocoto_realize"),
        (STR.validatexml, "_dispatch_rocoto_validate_xml"),
    ],
)
def test_cli__dispatch_rocoto(params):
    action, funcname = params
    args = {STR.action: action}
    with patch.object(cli, funcname) as func:
        cli._dispatch_rocoto(args)
    func.assert_called_once_with(args)


def test_cli_dispatch_rocoto_iterate(utc):
    cycle = utc()
    database = Path("/path/to/rocoto.db")
    rate = 11
    task = "foo"
    workflow = Path("/path/to/rocoto.xml")
    args = {
        STR.cycle: cycle,
        STR.database: database,
        STR.rate: rate,
        STR.task: task,
        STR.workflow: workflow,
    }
    with patch.object(uwtools.api.rocoto, "_iterate") as _iterate:
        cli._dispatch_rocoto_iterate(args)
    _iterate.assert_called_once_with(**args)


def test_cli__dispatch_rocoto_realize():
    args = {STR.config_file: 1, STR.output_file: 2, STR.key_path: None}
    with patch.object(uwtools.api.rocoto, "_realize") as _realize:
        cli._dispatch_rocoto_realize(args)
    _realize.assert_called_once_with(config=1, output_file=2, key_path=None)


def test_cli__dispatch_rocoto_realize_no_optional():
    args = {STR.config_file: None, STR.output_file: None, STR.key_path: None}
    with patch.object(uwtools.api.rocoto, "_realize") as func:
        cli._dispatch_rocoto_realize(args)
    func.assert_called_once_with(config=None, output_file=None, key_path=None)


def test_cli__dispatch_rocoto_validate_xml():
    args = {STR.input_file: 1}
    with patch.object(uwtools.api.rocoto, "_validate_xml_file") as _validate_xml_file:
        cli._dispatch_rocoto_validate_xml(args)
    _validate_xml_file.assert_called_once_with(xml_file=1)


def test_cli__dispatch_rocoto_validate_xml_invalid():
    args = {STR.input_file: 1, STR.verbose: False}
    with patch.object(uwtools.api.rocoto, "_validate_xml_file", return_value=False):
        assert cli._dispatch_rocoto_validate_xml(args) is False


def test_cli__dispatch_rocoto_validate_xml_no_optional():
    args = {STR.input_file: None, STR.verbose: False}
    with patch.object(uwtools.api.rocoto, "_validate_xml_file") as _validate_xml_file:
        cli._dispatch_rocoto_validate_xml(args)
    _validate_xml_file.assert_called_once_with(xml_file=None)


@mark.parametrize(
    "params",
    [(STR.render, "_dispatch_template_render"), (STR.translate, "_dispatch_template_translate")],
)
def test_cli__dispatch_template(params):
    action, funcname = params
    args = {STR.action: action}
    with patch.object(cli, funcname) as func:
        cli._dispatch_template(args)
    func.assert_called_once_with(args)


@mark.parametrize("valsneeded", [False, True])
def test_cli__dispatch_template_render_fail(valsneeded):
    args = {
        STR.input_file: 1,
        STR.output_file: 2,
        STR.values_file: 3,
        STR.values_format: 4,
        STR.cycle: 5,
        STR.leadtime: 6,
        STR.key_eq_val_pairs: ["foo=42", "bar=43"],
        STR.env: 7,
        STR.search_path: 8,
        STR.values_needed: valsneeded,
        STR.dry_run: 9,
    }
    with patch.object(uwtools.api.template, "render", side_effect=UWTemplateRenderError):
        assert cli._dispatch_template_render(args) is valsneeded


def test_cli__dispatch_template_render_no_optional():
    args: dict = {
        STR.input_file: None,
        STR.output_file: None,
        STR.values_file: None,
        STR.values_format: None,
        STR.cycle: None,
        STR.leadtime: None,
        STR.key_eq_val_pairs: [],
        STR.env: False,
        STR.search_path: None,
        STR.values_needed: False,
        STR.dry_run: False,
    }
    with patch.object(uwtools.api.template, "render") as render:
        cli._dispatch_template_render(args)
    render.assert_called_once_with(
        input_file=None,
        output_file=None,
        values_src=None,
        values_format=None,
        cycle=None,
        leadtime=None,
        overrides={},
        env=False,
        searchpath=None,
        values_needed=False,
        dry_run=False,
        stdin_ok=True,
    )


def test_cli__dispatch_template_render_yaml():
    args = {
        STR.input_file: 1,
        STR.output_file: 2,
        STR.values_file: 3,
        STR.values_format: 4,
        STR.cycle: 5,
        STR.leadtime: 6,
        STR.key_eq_val_pairs: ["foo=42", "bar=43"],
        STR.env: 7,
        STR.search_path: 8,
        STR.values_needed: 9,
        STR.dry_run: 10,
    }
    with patch.object(uwtools.api.template, "render") as render:
        cli._dispatch_template_render(args)
    render.assert_called_once_with(
        input_file=1,
        output_file=2,
        values_src=3,
        values_format=4,
        cycle=5,
        leadtime=6,
        overrides={"foo": "42", "bar": "43"},
        env=7,
        searchpath=8,
        values_needed=9,
        dry_run=10,
        stdin_ok=True,
    )


def test_cli__dispatch_template_translate():
    args = {
        STR.input_file: 1,
        STR.output_file: 2,
        STR.dry_run: 3,
    }
    with patch.object(
        uwtools.api.template, "_convert_atparse_to_jinja2"
    ) as _convert_atparse_to_jinja2:
        cli._dispatch_template_translate(args)
    _convert_atparse_to_jinja2.assert_called_once_with(input_file=1, output_file=2, dry_run=3)


def test_cli__dispatch_template_translate_no_optional():
    args = {
        STR.dry_run: False,
        STR.input_file: None,
        STR.output_file: None,
    }
    with patch.object(
        uwtools.api.template, "_convert_atparse_to_jinja2"
    ) as _convert_atparse_to_jinja2:
        cli._dispatch_template_translate(args)
    _convert_atparse_to_jinja2.assert_called_once_with(
        input_file=None, output_file=None, dry_run=False
    )


@mark.parametrize("hours", [0, 24, 168])
def test_cli__dispatch_to_driver(hours, utc):
    cycle = utc()
    leadtime = timedelta(hours=hours)
    args: dict = {
        "action": "foo",
        "batch": True,
        "config_file": "/path/to/config",
        "cycle": cycle,
        "leadtime": leadtime,
        "dry_run": False,
        "graph_file": None,
        "key_path": ["foo", "bar"],
        "schema_file": None,
        "show_schema": False,
        "stdin_ok": True,
    }
    adriver = Mock()
    with patch.object(cli, "import_module", return_value=adriver):
        cli._dispatch_to_driver(name="adriver", args=args)
        adriver.execute.assert_called_once_with(
            batch=True,
            config="/path/to/config",
            cycle=cycle,
            leadtime=leadtime,
            dry_run=False,
            graph_file=None,
            key_path=["foo", "bar"],
            schema_file=None,
            task="foo",
            stdin_ok=True,
        )


def test_cli__dispatch_to_driver_no_schema(capsys):
    adriver = Mock()
    with patch.object(cli, "import_module", return_value=adriver), raises(SystemExit):
        cli._dispatch_to_driver(name="adriver", args={})
    assert "No TASK specified" in capsys.readouterr().err


def test_cli__dispatch_to_driver_show_schema(capsys):
    adriver = Mock()
    adriver.schema.return_value = {"fruit": {"b": "banana", "a": "apple"}}
    with patch.object(cli, "import_module", return_value=adriver):
        assert cli._dispatch_to_driver(name="adriver", args={"show_schema": True}) is True
    expected = """
    {
      "fruit": {
        "a": "apple",
        "b": "banana"
      }
    }
    """
    assert capsys.readouterr().out == dedent(expected).lstrip()


@mark.parametrize("quiet", [False, True])
@mark.parametrize("verbose", [False, True])
def test_cli_main_fail_checks(capsys, quiet, verbose):
    # Using mode 'template render' for testing.
    raw_args = ["testing", STR.template, STR.render]
    if quiet:
        raw_args.append(cli._switch(STR.quiet))
    if verbose:
        raw_args.append(cli._switch(STR.verbose))
    with (
        patch.object(sys, "argv", raw_args),
        patch.object(cli, "_dispatch_template", return_value=True),
        raises(SystemExit) as e,
    ):
        cli.main()
    if quiet and verbose:
        assert e.value.code == 1
        assert "--quiet may not be used with --verbose" in capsys.readouterr().err
    else:
        assert e.value.code == 0


@mark.parametrize("vals", [(True, 0), (False, 1)])
def test_cli_main_fail_dispatch(vals):
    # Using mode 'template render' for testing.
    dispatch_retval, exit_status = vals
    raw_args = ["testing", STR.template, STR.render]
    with (
        patch.object(sys, "argv", raw_args),
        patch.object(cli, "_dispatch_template", return_value=dispatch_retval),
        raises(SystemExit) as e,
    ):
        cli.main()
    assert e.value.code == exit_status


def test_cli_main_fail_exception_abort():
    # Mock setup_logging() to raise a UWError in main() before logging is configured, which triggers
    # a call to _abort().
    msg = "Catastrophe"
    with (
        patch.object(cli, "setup_logging", side_effect=UWError(msg)),
        patch.object(cli, "_abort", side_effect=SystemExit) as _abort,
        raises(SystemExit),
    ):
        cli.main()
    _abort.assert_called_once_with(msg)


def test_cli_main_fail_exception_log():
    # Mock _dispatch_template() to raise a UWError in main() after logging is configured, which logs
    # an error message and exists with exit status.
    msg = "Catastrophe"
    with (
        patch.object(cli, "_dispatch_template", side_effect=UWError(msg)),
        patch.object(cli, "log") as log,
        patch.object(sys, "argv", ["uw", "template", "render"]),
        raises(SystemExit) as e,
    ):
        cli.main()
    assert e.value.code == 1
    log.error.assert_called_once_with(msg)


def test_cli__parse_args():
    raw_args = ["testing", "--bar", "42"]
    with patch.object(cli, "Parser") as p:
        cli._parse_args(raw_args)
        p.assert_called_once()
        parser = p()
        parser.parse_args.assert_called_with(raw_args)


def test_cli__switch():
    assert cli._switch("foo_bar") == "--foo-bar"


def test_cli__timedelta_from_str(capsys):
    assert cli._timedelta_from_str("111:222:333").total_seconds() == 111 * 3600 + 222 * 60 + 333
    assert cli._timedelta_from_str("111:222").total_seconds() == 111 * 3600 + 222 * 60
    assert cli._timedelta_from_str("111").total_seconds() == 111 * 3600
    assert cli._timedelta_from_str("01:15:07").total_seconds() == 1 * 3600 + 15 * 60 + 7
    with raises(SystemExit):
        cli._timedelta_from_str("foo")
    assert f"Specify leadtime as {cli.LEADTIME_DESC}" in capsys.readouterr().err


def test_cli__version():
    assert re.match(r"version \d+\.\d+\.\d+ build \d+", cli._version())
