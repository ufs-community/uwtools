# pylint: disable=missing-function-docstring,protected-access,redefined-outer-name

import datetime as dt
import logging
import re
import sys
from argparse import ArgumentParser as Parser
from argparse import _SubParsersAction
from pathlib import Path
from unittest.mock import Mock, patch

from pytest import fixture, mark, raises

import uwtools.api
import uwtools.api.config
import uwtools.api.rocoto
import uwtools.api.template
from uwtools import cli
from uwtools.cli import STR
from uwtools.exceptions import UWConfigRealizeError, UWError, UWTemplateRenderError
from uwtools.logging import log
from uwtools.tests.support import regex_logged
from uwtools.utils.file import FORMAT

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
def args_dispatch_file():
    return {
        "target_dir": "/target/dir",
        "config_file": "/config/file",
        "cycle": dt.datetime.now(),
        "leadtime": dt.timedelta(hours=6),
        "keys": ["a", "b"],
        "dry_run": False,
        "stdin_ok": True,
    }


@fixture
def subparsers():
    # Create and return a subparsers test object.
    return Parser().add_subparsers()


# Test functions


def test__abort(capsys):
    msg = "Aborting..."
    with raises(SystemExit) as e:
        cli._abort(msg)
    assert e.value.code == 1
    assert msg in capsys.readouterr().err


def test__add_subparser_config(subparsers):
    cli._add_subparser_config(subparsers)
    assert actions(subparsers.choices[STR.config]) == [STR.compare, STR.realize, STR.validate]


def test__add_subparser_config_compare(subparsers):
    cli._add_subparser_config_compare(subparsers)
    assert subparsers.choices[STR.compare]


def test__add_subparser_config_realize(subparsers):
    cli._add_subparser_config_realize(subparsers)
    assert subparsers.choices[STR.realize]


def test__add_subparser_config_validate(subparsers):
    cli._add_subparser_config_validate(subparsers)
    assert subparsers.choices[STR.validate]


def test__add_subparser_file(subparsers):
    cli._add_subparser_file(subparsers)
    assert actions(subparsers.choices[STR.file]) == [STR.copy, STR.link, STR.mkdir]


def test__add_subparser_file_copy(subparsers):
    cli._add_subparser_file_copy(subparsers)
    assert subparsers.choices[STR.copy]


def test__add_subparser_file_link(subparsers):
    cli._add_subparser_file_link(subparsers)
    assert subparsers.choices[STR.link]


def test__add_subparser_for_driver(subparsers):
    name = "adriver"
    adriver = Mock()
    adriver.tasks.return_value = {"task1": "task1 description", "task2": "task2 description"}
    with patch.object(cli, "import_module", return_value=adriver):
        cli._add_subparser_for_driver(name, subparsers, with_cycle=True)
    assert actions(subparsers.choices[name]) == ["task1", "task2"]


def test__add_subparser_for_driver_task(subparsers):
    assert not subparsers.choices
    cli._add_subparser_for_driver_task(subparsers, "task1", "task1 description", with_cycle=True)
    assert subparsers.choices["task1"]


def test__add_subparser_rocoto(subparsers):
    cli._add_subparser_rocoto(subparsers)
    assert subparsers.choices[STR.rocoto]


def test__add_subparser_rocoto_realize(subparsers):
    cli._add_subparser_rocoto_realize(subparsers)
    assert subparsers.choices[STR.realize]


def test__add_subparser_rocoto_validate(subparsers):
    cli._add_subparser_rocoto_validate(subparsers)
    assert subparsers.choices[STR.validate]


def test__add_subparser_template(subparsers):
    cli._add_subparser_template(subparsers)
    assert actions(subparsers.choices[STR.template]) == [STR.render, STR.translate]


def test__add_subparser_template_render(subparsers):
    cli._add_subparser_template_render(subparsers)
    assert subparsers.choices[STR.render]


def test__add_subparser_template_translate(subparsers):
    cli._add_subparser_template_translate(subparsers)
    assert subparsers.choices[STR.translate]


def test__dispatch_execute():
    cycle = dt.datetime.now()
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
        "task": "eighty_eight",
        "stdin_ok": True,
    }
    with patch.object(cli.uwtools.api.driver, "execute") as execute:
        cli._dispatch_execute(args=args)
        execute.assert_called_once_with(
            classname="TestDriver",
            module="testdriver",
            task="eighty_eight",
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
    "vals",
    [
        (STR.file1path, STR.file1fmt),
        (STR.file2path, STR.file2fmt),
        (STR.infile, STR.infmt),
        (STR.outfile, STR.outfmt),
        (STR.valsfile, STR.valsfmt),
    ],
)
def test__check_file_vs_format_fail(capsys, vals):
    # When reading/writing from/to stdin/stdout, the data format must be specified, since there is
    # no filename to deduce it from.
    file_arg, format_arg = vals
    args = dict(file_arg=None, format_arg=None)
    with raises(SystemExit):
        cli._check_file_vs_format(file_arg=file_arg, format_arg=format_arg, args=args)
    assert (
        "Specify %s when %s is not specified" % (cli._switch(format_arg), cli._switch(file_arg))
        in capsys.readouterr().err
    )


def test__check_file_vs_format_pass_explicit():
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
def test__check_file_vs_format_pass_implicit(fmt):
    # The format is correctly deduced for a file with a known extension.
    args = {STR.infile: f"/path/to/input.{fmt}", STR.infmt: None}
    args = cli._check_file_vs_format(
        file_arg=STR.infile,
        format_arg=STR.infmt,
        args=args,
    )
    assert args[STR.infmt] == vars(FORMAT)[fmt]


def test__check_template_render_vals_args_implicit_fail():
    # The values-file format cannot be deduced from the filename.
    args = {STR.valsfile: "a.jpg"}
    with raises(UWError) as e:
        cli._check_template_render_vals_args(args)
    assert "Cannot deduce format" in str(e.value)


def test__check_template_render_vals_args_implicit_pass():
    # The values-file format is deduced from the filename.
    args = {STR.valsfile: "a.yaml"}
    checked = cli._check_template_render_vals_args(args)
    assert checked[STR.valsfmt] == FORMAT.yaml


def test__check_template_render_vals_args_noop_no_valsfile():
    # No values file is provided, so format is irrelevant.
    args = {STR.valsfile: None}
    assert cli._check_template_render_vals_args(args) == args


def test__check_template_render_vals_args_noop_explicit_valsfmt():
    # An explicit values format is honored, valid or not.
    args = {STR.valsfile: "a.txt", STR.valsfmt: "jpg"}
    assert cli._check_template_render_vals_args(args) == args


@mark.parametrize(
    "fmt,fn,ok",
    [
        (None, "update.txt", False),
        ("yaml", "udpate.txt", True),
        (None, "update.yaml", True),
        ("yaml", "update.yaml", True),
        ("jpg", "udpate.yaml", True),
    ],
)
def test__check_update(fmt, fn, ok):
    args = {STR.updatefile: fn, STR.updatefmt: fmt}
    if ok:
        assert cli._check_update(args) == args
    else:
        with raises(UWError) as e:
            cli._check_update(args)
        assert "Cannot deduce format" in str(e.value)


def test__check_verbosity_fail(capsys):
    log.setLevel(logging.INFO)
    args = {STR.quiet: True, STR.verbose: True}
    with raises(SystemExit):
        cli._check_verbosity(args)
    assert "--quiet may not be used with --verbose" in capsys.readouterr().err


@mark.parametrize("flags", ([STR.quiet], [STR.verbose]))
def test__check_verbosity_ok(flags):
    args = {flag: True for flag in flags}
    assert cli._check_verbosity(args) == args


def test__dict_from_key_eq_val_strings():
    assert not cli._dict_from_key_eq_val_strings([])
    assert cli._dict_from_key_eq_val_strings(["a=1", "b=2"]) == {"a": "1", "b": "2"}


@mark.parametrize(
    "params",
    [
        (STR.compare, "_dispatch_config_compare"),
        (STR.realize, "_dispatch_config_realize"),
        (STR.validate, "_dispatch_config_validate"),
    ],
)
def test__dispatch_config(params):
    action, funcname = params
    args = {STR.action: action}
    with patch.object(cli, funcname) as func:
        cli._dispatch_config(args)
    func.assert_called_once_with(args)


def test__dispatch_config_compare():
    args = {STR.file1path: 1, STR.file1fmt: 2, STR.file2path: 3, STR.file2fmt: 4}
    with patch.object(cli.uwtools.api.config, "compare") as compare:
        cli._dispatch_config_compare(args)
    compare.assert_called_once_with(
        config_1_path=args[STR.file1path],
        config_1_format=args[STR.file1fmt],
        config_2_path=args[STR.file2path],
        config_2_format=args[STR.file2fmt],
    )


def test__dispatch_config_realize(args_config_realize):
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


def test__dispatch_config_realize_fail(caplog, args_config_realize):
    log.setLevel(logging.ERROR)
    with patch.object(cli.uwtools.api.config, "realize", side_effect=UWConfigRealizeError):
        assert cli._dispatch_config_realize(args_config_realize) is False
    assert regex_logged(caplog, "Config could not be realized")


def test__dispatch_config_validate_config_obj():
    _dispatch_config_validate_args = {
        STR.schemafile: Path("/path/to/a.jsonschema"),
        STR.infile: Path("/path/to/config.yaml"),
    }
    with patch.object(uwtools.api.config, "_validate_external") as _validate_external:
        cli._dispatch_config_validate(_dispatch_config_validate_args)
    _validate_external_args = {
        STR.schemafile: _dispatch_config_validate_args[STR.schemafile],
        STR.config: _dispatch_config_validate_args[STR.infile],
    }
    _validate_external.assert_called_once_with(**_validate_external_args)


@mark.parametrize(
    "action, funcname",
    [
        (STR.copy, "_dispatch_file_copy"),
        (STR.link, "_dispatch_file_link"),
        (STR.mkdir, "_dispatch_file_mkdir"),
    ],
)
def test__dispatch_file(action, funcname):
    args = {STR.action: action}
    with patch.object(cli, funcname) as func:
        cli._dispatch_file(args)
    func.assert_called_once_with(args)


def test__dispatch_file_copy(args_dispatch_file):
    args = args_dispatch_file
    with patch.object(cli.uwtools.api.file, "copy") as copy:
        cli._dispatch_file_copy(args)
    copy.assert_called_once_with(
        target_dir=args["target_dir"],
        config=args["config_file"],
        cycle=args["cycle"],
        leadtime=args["leadtime"],
        keys=args["keys"],
        dry_run=args["dry_run"],
        stdin_ok=args["stdin_ok"],
    )


def test__dispatch_file_link(args_dispatch_file):
    args = args_dispatch_file
    with patch.object(cli.uwtools.api.file, "link") as link:
        cli._dispatch_file_link(args)
    link.assert_called_once_with(
        target_dir=args["target_dir"],
        config=args["config_file"],
        cycle=args["cycle"],
        leadtime=args["leadtime"],
        keys=args["keys"],
        dry_run=args["dry_run"],
        stdin_ok=args["stdin_ok"],
    )


def test__dispatch_file_mkdir(args_dispatch_file):
    args = args_dispatch_file
    with patch.object(cli.uwtools.api.file, "mkdir") as mkdir:
        cli._dispatch_file_mkdir(args)
    mkdir.assert_called_once_with(
        target_dir=args["target_dir"],
        config=args["config_file"],
        cycle=args["cycle"],
        leadtime=args["leadtime"],
        keys=args["keys"],
        dry_run=args["dry_run"],
        stdin_ok=args["stdin_ok"],
    )


@mark.parametrize(
    "params",
    [
        (STR.realize, "_dispatch_rocoto_realize"),
        (STR.validate, "_dispatch_rocoto_validate"),
    ],
)
def test__dispatch_rocoto(params):
    action, funcname = params
    args = {STR.action: action}
    with patch.object(cli, funcname) as func:
        cli._dispatch_rocoto(args)
    func.assert_called_once_with(args)


def test__dispatch_rocoto_realize():
    args = {STR.cfgfile: 1, STR.outfile: 2}
    with patch.object(uwtools.api.rocoto, "_realize") as _realize:
        cli._dispatch_rocoto_realize(args)
    _realize.assert_called_once_with(config=1, output_file=2)


def test__dispatch_rocoto_realize_no_optional():
    args = {STR.cfgfile: None, STR.outfile: None}
    with patch.object(uwtools.api.rocoto, "_realize") as func:
        cli._dispatch_rocoto_realize(args)
    func.assert_called_once_with(config=None, output_file=None)


def test__dispatch_rocoto_validate_xml():
    args = {STR.infile: 1}
    with patch.object(uwtools.api.rocoto, "_validate") as _validate:
        cli._dispatch_rocoto_validate(args)
    _validate.assert_called_once_with(xml_file=1)


def test__dispatch_rocoto_validate_xml_invalid():
    args = {STR.infile: 1, STR.verbose: False}
    with patch.object(uwtools.api.rocoto, "_validate", return_value=False):
        assert cli._dispatch_rocoto_validate(args) is False


def test__dispatch_rocoto_validate_xml_no_optional():
    args = {STR.infile: None, STR.verbose: False}
    with patch.object(uwtools.api.rocoto, "_validate") as validate:
        cli._dispatch_rocoto_validate(args)
    validate.assert_called_once_with(xml_file=None)


@mark.parametrize(
    "params",
    [(STR.render, "_dispatch_template_render"), (STR.translate, "_dispatch_template_translate")],
)
def test__dispatch_template(params):
    action, funcname = params
    args = {STR.action: action}
    with patch.object(cli, funcname) as func:
        cli._dispatch_template(args)
    func.assert_called_once_with(args)


@mark.parametrize("valsneeded", [False, True])
def test__dispatch_template_render_fail(valsneeded):
    args = {
        STR.infile: 1,
        STR.outfile: 2,
        STR.valsfile: 3,
        STR.valsfmt: 4,
        STR.keyvalpairs: ["foo=88", "bar=99"],
        STR.env: 5,
        STR.searchpath: 6,
        STR.valsneeded: valsneeded,
        STR.dryrun: 7,
    }
    with patch.object(uwtools.api.template, "render", side_effect=UWTemplateRenderError):
        assert cli._dispatch_template_render(args) is valsneeded


def test__dispatch_template_render_no_optional():
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


def test__dispatch_template_render_yaml():
    args = {
        STR.infile: 1,
        STR.outfile: 2,
        STR.valsfile: 3,
        STR.valsfmt: 4,
        STR.keyvalpairs: ["foo=88", "bar=99"],
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
        overrides={"foo": "88", "bar": "99"},
        env=5,
        searchpath=6,
        values_needed=7,
        dry_run=8,
        stdin_ok=True,
    )


def test__dispatch_template_translate():
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


def test__dispatch_template_translate_no_optional():
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
def test__dispatch_to_driver(hours):
    name = "adriver"
    cycle = dt.datetime.now()
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
        "stdin_ok": True,
    }
    adriver = Mock()
    with patch.object(cli, "import_module", return_value=adriver):
        cli._dispatch_to_driver(name=name, args=args)
        adriver.execute.assert_called_once_with(
            batch=True,
            config="/path/to/config",
            cycle=cycle,
            leadtime=leadtime,
            dry_run=False,
            graph_file=None,
            key_path=["foo", "bar"],
            task="foo",
            stdin_ok=True,
        )


@mark.parametrize("quiet", [False, True])
@mark.parametrize("verbose", [False, True])
def test_main_fail_checks(capsys, quiet, verbose):
    # Using mode 'template render' for testing.
    raw_args = ["testing", STR.template, STR.render]
    if quiet:
        raw_args.append(cli._switch(STR.quiet))
    if verbose:
        raw_args.append(cli._switch(STR.verbose))
    with patch.object(sys, "argv", raw_args):
        with patch.object(cli, "_dispatch_template", return_value=True):
            with raises(SystemExit) as e:
                cli.main()
            if quiet and verbose:
                assert e.value.code == 1
                assert "--quiet may not be used with --verbose" in capsys.readouterr().err
            else:
                assert e.value.code == 0


@mark.parametrize("vals", [(True, 0), (False, 1)])
def test_main_fail_dispatch(vals):
    # Using mode 'template render' for testing.
    dispatch_retval, exit_status = vals
    raw_args = ["testing", STR.template, STR.render]
    with patch.object(sys, "argv", raw_args):
        with patch.object(cli, "_dispatch_template", return_value=dispatch_retval):
            with raises(SystemExit) as e:
                cli.main()
            assert e.value.code == exit_status


def test_main_fail_exception_abort():
    # Mock setup_logging() to raise a UWError in main() before logging is configured, which triggers
    # a call to _abort().
    msg = "Catastrophe"
    with patch.object(cli, "setup_logging", side_effect=UWError(msg)):
        with patch.object(cli, "_abort", side_effect=SystemExit) as _abort:
            with raises(SystemExit):
                cli.main()
        _abort.assert_called_once_with(msg)


def test_main_fail_exception_log():
    # Mock _dispatch_template() to raise a UWError in main() after logging is configured, which logs
    # an error message and exists with exit status.
    msg = "Catastrophe"
    with patch.object(cli, "_dispatch_template", side_effect=UWError(msg)):
        with patch.object(cli, "log") as log:
            with patch.object(sys, "argv", ["uw", "template", "render"]):
                with raises(SystemExit) as e:
                    cli.main()
                assert e.value.code == 1
            log.error.assert_called_once_with(msg)


def test__parse_args():
    raw_args = ["testing", "--bar", "88"]
    with patch.object(cli, "Parser") as Parser:
        cli._parse_args(raw_args)
        Parser.assert_called_once()
        parser = Parser()
        parser.parse_args.assert_called_with(raw_args)


def test__switch():
    assert cli._switch("foo_bar") == "--foo-bar"


def test__timedelta_from_str(capsys):
    assert cli._timedelta_from_str("111:222:333").total_seconds() == 111 * 3600 + 222 * 60 + 333
    assert cli._timedelta_from_str("111:222").total_seconds() == 111 * 3600 + 222 * 60
    assert cli._timedelta_from_str("111").total_seconds() == 111 * 3600
    assert cli._timedelta_from_str("01:15:07").total_seconds() == 1 * 3600 + 15 * 60 + 7
    with raises(SystemExit):
        cli._timedelta_from_str("foo")
    assert f"Specify leadtime as {cli.LEADTIME_DESC}" in capsys.readouterr().err


def test__version():
    assert re.match(r"version \d+\.\d+\.\d+ build \d+", cli._version())
