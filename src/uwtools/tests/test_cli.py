import datetime as dt
import re
import sys
from argparse import ArgumentParser as Parser
from argparse import _SubParsersAction
from pathlib import Path
from textwrap import dedent
from unittest.mock import Mock, patch

from pytest import fixture, mark, raises

import uwtools.api
import uwtools.api.config
import uwtools.api.rocoto
import uwtools.api.template
from uwtools import cli
from uwtools.cli import STR
from uwtools.exceptions import UWConfigRealizeError, UWError, UWTemplateRenderError
from uwtools.strings import FORMAT

# Helpers


def actions(parser: Parser) -> list[str]:
    # Return actions (named subparsers) belonging to the given parser.
    if actions := [x for x in parser._actions if isinstance(x, _SubParsersAction)]:
        return list(actions[0].choices.keys())
    return []


# Fixtures


@fixture
def args_config_realize():
    return {
        STR.infile: "in",
        STR.infmt: "yaml",
        STR.updatefile: "update",
        STR.updatefmt: "yaml",
        STR.outfile: "out",
        STR.outfmt: "yaml",
        STR.keypath: "foo.bar",
        STR.valsneeded: False,
        STR.total: False,
        STR.dryrun: False,
    }


@fixture
def args_dispatch_fs(utc):
    return {
        "target_dir": "/target/dir",
        "config_file": "/config/file",
        "cycle": utc(),
        "leadtime": dt.timedelta(hours=6),
        "key_path": ["a", "b"],
        "dry_run": False,
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


def test_cli__add_subparser_rocoto_validate(subparsers):
    cli._add_subparser_rocoto_validate(subparsers)
    assert subparsers.choices[STR.validate]


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
        (STR.path1, STR.fmt1),
        (STR.path2, STR.fmt2),
        (STR.infile, STR.infmt),
        (STR.outfile, STR.outfmt),
        (STR.valsfile, STR.valsfmt),
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
    args = {STR.infile: "/path/to/input.txt", STR.infmt: fmt}
    args = cli._check_file_vs_format(
        file_arg=STR.infile,
        format_arg=STR.infmt,
        args=args,
    )
    assert args[STR.infmt] == fmt


@mark.parametrize("fmt", FORMAT.formats())
def test_cli__check_file_vs_format_pass_implicit(fmt):
    # The format is correctly deduced for a file with a known extension.
    args = {STR.infile: f"/path/to/input.{fmt}", STR.infmt: None}
    args = cli._check_file_vs_format(file_arg=STR.infile, format_arg=STR.infmt, args=args)
    assert args[STR.infmt] == vars(FORMAT)[fmt]


def test_cli__check_template_render_vals_args_implicit_fail():
    # The values-file format cannot be deduced from the filename.
    args = {STR.valsfile: "a.jpg"}
    expected = {"values_file": "a.jpg", "values_format": FORMAT.yaml}
    assert cli._check_template_render_vals_args(args) == expected


def test_cli__check_template_render_vals_args_implicit_pass():
    # The values-file format is deduced from the filename.
    args = {STR.valsfile: "a.yaml"}
    checked = cli._check_template_render_vals_args(args)
    assert checked[STR.valsfmt] == FORMAT.yaml


def test_cli__check_template_render_vals_args_noop_no_valsfile():
    # No values file is provided, so format is irrelevant.
    args = {STR.valsfile: None}
    assert cli._check_template_render_vals_args(args) == args


def test_cli__check_template_render_vals_args_noop_explicit_valsfmt():
    # An explicit values format is honored, valid or not.
    args = {STR.valsfile: "a.txt", STR.valsfmt: "jpg"}
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
    args = {STR.updatefile: fn, STR.updatefmt: fmt}
    assert cli._check_update(args) == {STR.updatefile: fn, STR.updatefmt: expected}


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
    args = {STR.path1: 1, STR.fmt1: 2, STR.path2: 3, STR.fmt2: 4}
    with patch.object(cli.uwtools.api.config, "compare") as compare:
        cli._dispatch_config_compare(args)
    compare.assert_called_once_with(
        path1=args[STR.path1],
        format1=args[STR.fmt1],
        path2=args[STR.path2],
        format2=args[STR.fmt2],
    )


def test_cli__dispatch_config_compose():
    configs = ["/path/to/a", "/path/to/b"]
    outfile = "/path/to/output"
    args = {
        STR.configs: configs,
        STR.outfile: outfile,
        STR.infmt: FORMAT.yaml,
        STR.outfmt: FORMAT.yaml,
    }
    with patch.object(cli.uwtools.api.config, "compose") as compose:
        cli._dispatch_config_compose(args)
    compose.assert_called_once_with(
        configs=configs, output_file=outfile, input_format=FORMAT.yaml, output_format=FORMAT.yaml
    )


def test_cli__dispatch_config_realize(args_config_realize):
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
        values_needed=False,
        total=False,
        dry_run=False,
        stdin_ok=True,
    )


def test_cli__dispatch_config_realize_fail(args_config_realize, logged):
    with patch.object(cli.uwtools.api.config, "realize", side_effect=UWConfigRealizeError):
        assert cli._dispatch_config_realize(args_config_realize) is False
    assert logged("Config could not be realized")


def test_cli__dispatch_config_validate_config_obj():
    _dispatch_config_validate_args = {
        STR.schemafile: Path("/path/to/a.jsonschema"),
        STR.infile: Path("/path/to/config.yaml"),
    }
    with patch.object(uwtools.api.config, "_validate_external") as _validate_external:
        cli._dispatch_config_validate(_dispatch_config_validate_args)
    _validate_external_args = {
        STR.schemafile: _dispatch_config_validate_args[STR.schemafile],
        "config_data": None,
        "config_path": _dispatch_config_validate_args[STR.infile],
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
      "not-ready": [
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
        (STR.realize, "_dispatch_rocoto_realize"),
        (STR.validate, "_dispatch_rocoto_validate"),
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
    args = {STR.cfgfile: 1, STR.outfile: 2}
    with patch.object(uwtools.api.rocoto, "_realize") as _realize:
        cli._dispatch_rocoto_realize(args)
    _realize.assert_called_once_with(config=1, output_file=2)


def test_cli__dispatch_rocoto_realize_no_optional():
    args = {STR.cfgfile: None, STR.outfile: None}
    with patch.object(uwtools.api.rocoto, "_realize") as func:
        cli._dispatch_rocoto_realize(args)
    func.assert_called_once_with(config=None, output_file=None)


def test_cli__dispatch_rocoto_validate_xml():
    args = {STR.infile: 1}
    with patch.object(uwtools.api.rocoto, "_validate") as _validate:
        cli._dispatch_rocoto_validate(args)
    _validate.assert_called_once_with(xml_file=1)


def test_cli__dispatch_rocoto_validate_xml_invalid():
    args = {STR.infile: 1, STR.verbose: False}
    with patch.object(uwtools.api.rocoto, "_validate", return_value=False):
        assert cli._dispatch_rocoto_validate(args) is False


def test_cli__dispatch_rocoto_validate_xml_no_optional():
    args = {STR.infile: None, STR.verbose: False}
    with patch.object(uwtools.api.rocoto, "_validate") as validate:
        cli._dispatch_rocoto_validate(args)
    validate.assert_called_once_with(xml_file=None)


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
        STR.infile: 1,
        STR.outfile: 2,
        STR.valsfile: 3,
        STR.valsfmt: 4,
        STR.keyvalpairs: ["foo=42", "bar=43"],
        STR.env: 5,
        STR.searchpath: 6,
        STR.valsneeded: valsneeded,
        STR.dryrun: 7,
    }
    with patch.object(uwtools.api.template, "render", side_effect=UWTemplateRenderError):
        assert cli._dispatch_template_render(args) is valsneeded


def test_cli__dispatch_template_render_no_optional():
    args: dict = {
        STR.infile: None,
        STR.outfile: None,
        STR.valsfile: None,
        STR.valsfmt: None,
        STR.keyvalpairs: [],
        STR.env: False,
        STR.searchpath: None,
        STR.valsneeded: False,
        STR.dryrun: False,
    }
    with patch.object(uwtools.api.template, "render") as render:
        cli._dispatch_template_render(args)
    render.assert_called_once_with(
        input_file=None,
        output_file=None,
        values_src=None,
        values_format=None,
        overrides={},
        env=False,
        searchpath=None,
        values_needed=False,
        dry_run=False,
        stdin_ok=True,
    )


def test_cli__dispatch_template_render_yaml():
    args = {
        STR.infile: 1,
        STR.outfile: 2,
        STR.valsfile: 3,
        STR.valsfmt: 4,
        STR.keyvalpairs: ["foo=42", "bar=43"],
        STR.env: 5,
        STR.searchpath: 6,
        STR.valsneeded: 7,
        STR.dryrun: 8,
    }
    with patch.object(uwtools.api.template, "render") as render:
        cli._dispatch_template_render(args)
    render.assert_called_once_with(
        input_file=1,
        output_file=2,
        values_src=3,
        values_format=4,
        overrides={"foo": "42", "bar": "43"},
        env=5,
        searchpath=6,
        values_needed=7,
        dry_run=8,
        stdin_ok=True,
    )


def test_cli__dispatch_template_translate():
    args = {
        STR.infile: 1,
        STR.outfile: 2,
        STR.dryrun: 3,
    }
    with patch.object(
        uwtools.api.template, "_convert_atparse_to_jinja2"
    ) as _convert_atparse_to_jinja2:
        cli._dispatch_template_translate(args)
    _convert_atparse_to_jinja2.assert_called_once_with(input_file=1, output_file=2, dry_run=3)


def test_cli__dispatch_template_translate_no_optional():
    args = {
        STR.dryrun: False,
        STR.infile: None,
        STR.outfile: None,
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
    leadtime = dt.timedelta(hours=hours)
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
