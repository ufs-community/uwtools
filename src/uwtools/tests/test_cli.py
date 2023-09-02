# pylint: disable=missing-function-docstring,protected-access,redefined-outer-name

import logging
from argparse import ArgumentParser as Parser
from argparse import Namespace as ns
from typing import List
from unittest.mock import DEFAULT as D
from unittest.mock import patch

import pytest
from pytest import fixture, raises

from uwtools import cli
from uwtools.utils.file import FORMAT

# Test functions


def test__abort(capsys):
    msg = "Aborting..."
    with raises(SystemExit):
        cli._abort(msg)
    assert msg in capsys.readouterr().err


def test__add_subparser_config(subparsers):
    cli._add_subparser_config(subparsers)
    assert submodes(subparsers.choices[cli.STR.config]) == [
        cli.STR.compare,
        cli.STR.realize,
        cli.STR.translate,
        cli.STR.validate,
    ]


def test__add_subparser_config_compare(subparsers):
    cli._add_subparser_config_compare(subparsers)
    assert subparsers.choices[cli.STR.compare]


def test__add_subparser_config_realize(subparsers):
    cli._add_subparser_config_realize(subparsers)
    assert subparsers.choices[cli.STR.realize]


def test__add_subparser_config_translate(subparsers):
    cli._add_subparser_config_translate(subparsers)
    assert subparsers.choices[cli.STR.translate]


def test__add_subparser_config_validate(subparsers):
    cli._add_subparser_config_validate(subparsers)
    assert subparsers.choices[cli.STR.validate]


def test__add_subparser_forecast(subparsers):
    cli._add_subparser_forecast(subparsers)
    assert submodes(subparsers.choices[cli.STR.forecast]) == [cli.STR.run]


def test__add_subparser_forecast_run(subparsers):
    cli._add_subparser_forecast_run(subparsers)
    assert subparsers.choices[cli.STR.run]


def test__add_subparser_template(subparsers):
    cli._add_subparser_template(subparsers)
    assert submodes(subparsers.choices[cli.STR.template]) == [cli.STR.render]


def test__add_subparser_template_render(subparsers):
    cli._add_subparser_template_render(subparsers)
    assert subparsers.choices[cli.STR.render]


def test__check_quiet_vs_verbose_fail_quiet_verbose(capsys):
    logging.getLogger().setLevel(logging.INFO)
    args = ns(quiet=True, verbose=True)
    with raises(SystemExit):
        cli._check_quiet_vs_verbose(args)
    assert (
        "Specify at most one of %s, %s" % (cli._arg2sw(cli.STR.quiet), cli._arg2sw(cli.STR.verbose))
        in capsys.readouterr().err
    )


def test__quiet_vs_verbose_ok():
    args = ns(foo=88)
    assert cli._check_quiet_vs_verbose(args) == args


def test__dict_from_key_eq_val_strings():
    assert not cli._dict_from_key_eq_val_strings([])
    assert cli._dict_from_key_eq_val_strings(["a=1", "b=2"]) == {"a": "1", "b": "2"}


@pytest.mark.parametrize(
    "params",
    [
        (cli.STR.compare, "_dispatch_config_compare"),
        (cli.STR.realize, "_dispatch_config_realize"),
        (cli.STR.translate, "_dispatch_config_translate"),
        (cli.STR.validate, "_dispatch_config_validate"),
    ],
)
def test__dispatch_config(params):
    submode, funcname = params
    args = ns(submode=submode)
    with patch.object(cli, funcname) as m:
        cli._dispatch_config(args)
    assert m.called_once_with(args)


def test__dispatch_config_compare():
    args = ns(file_1_path=1, file_1_format=2, file_2_path=3, file_2_format=4)
    with patch.object(cli.uwtools.config.core, "compare_configs") as m:
        cli._dispatch_config_compare(args)
    assert m.called_once_with(args)


def test__dispatch_config_realize():
    args = ns(
        input_file=1,
        input_format=2,
        output_file=3,
        output_format=4,
        values_file=5,
        values_format=6,
        values_needed=7,
        dry_run=8,
    )
    with patch.object(cli.uwtools.config.core, "realize_config") as m:
        cli._dispatch_config_realize(args)
    assert m.called_once_with(args)


def test__dispatch_config_translate_arparse_to_jinja2():
    args = ns(
        input_file=1,
        input_format=FORMAT.atparse,
        output_file=3,
        output_format=FORMAT.jinja2,
        dry_run=5,
    )
    with patch.object(cli.uwtools.config.atparse_to_jinja2, "convert") as m:
        cli._dispatch_config_translate(args)
    assert m.called_once_with(args)


def test_dispath_config_translate_unsupported():
    args = ns(input_file=1, input_format="jpg", output_file=3, output_format="png", dry_run=5)
    assert cli._dispatch_config_translate(args) is False


def test__dispatch_config_validate_yaml():
    args = ns(input_file=1, input_format=FORMAT.yaml, schema_file=3)
    with patch.object(cli.uwtools.config.validator, "validate_yaml") as m:
        cli._dispatch_config_validate(args)
    assert m.called_once_with(args)


def test_dispath_config_validate_unsupported():
    args = ns(input_file=1, input_format="jpg", schema_file=3)
    assert cli._dispatch_config_validate(args) is False


@pytest.mark.parametrize("params", [(cli.STR.run, "_dispatch_forecast_run")])
def test__dispatch_forecast(params):
    submode, funcname = params
    args = ns(submode=submode)
    with patch.object(cli, funcname) as m:
        cli._dispatch_forecast(args)
    assert m.called_once_with(args)


def test__dispatch_forecast_run():
    args = ns(config_file=1, forecast_model="foo")
    with patch.object(cli.uwtools.drivers.forecast, "FooForecast", create=True) as m:
        CLASSES = {"foo": getattr(cli.uwtools.drivers.forecast, "FooForecast")}
        with patch.object(cli.uwtools.drivers.forecast, "CLASSES", new=CLASSES):
            cli._dispatch_forecast_run(args)
    assert m.called_once_with(args)
    m().run.assert_called_once_with()


@pytest.mark.parametrize("params", [(cli.STR.render, "_dispatch_template_render")])
def test__dispatch_template(params):
    submode, funcname = params
    args = ns(submode=submode)
    with patch.object(cli, funcname) as m:
        cli._dispatch_template(args)
    assert m.called_once_with(args)


def test__dispatch_template_render_yaml():
    args = ns(
        input_file=1,
        output_file=2,
        values_file=3,
        values_format=4,
        key_eq_val_pairs=["foo=88", "bar=99"],
        values_needed=6,
        dry_run=7,
    )
    with patch.object(cli.uwtools.config.templater, cli.STR.render) as m:
        cli._dispatch_template_render(args)
    assert m.called_once_with(args)


@pytest.mark.parametrize("params", [(False, 1, False, True), (True, 0, True, False)])
def test_main_fail(params):
    dispatch_retval, status, quiet, verbose = params
    with patch.multiple(cli, _parse_args=D, _dispatch_config=D, setup_logging=D) as mocks:
        args = ns(mode=cli.STR.config, submode=cli.STR.realize, quiet=quiet, verbose=verbose)
        mocks["_parse_args"].return_value = args, {
            cli.STR.config: {cli.STR.realize: [lambda _: True]}
        }
        mocks["_dispatch_config"].return_value = dispatch_retval
        with raises(SystemExit) as e:
            cli.main()
        assert e.value.code == status
        mocks["_dispatch_config"].assert_called_once_with(args)
        mocks["setup_logging"].assert_called_with(quiet=quiet, verbose=verbose)


def test_main_raises_exception(capsys):
    msg = "Test failed intentionally"
    with patch.object(cli, "_parse_args", side_effect=Exception(msg)):
        with raises(SystemExit):
            cli.main()
    assert msg in capsys.readouterr().err


def test__parse_args():
    raw_args = ["foo", "--bar", "88"]
    with patch.object(cli, "Parser") as Parser:
        cli._parse_args(raw_args)
        Parser.assert_called_once()
        parser = Parser()
        parser.parse_args.assert_called_with(raw_args)


@pytest.mark.parametrize(
    "vals",
    [
        (ns(file_1_path=None, file_1_format=None), cli.STR.file1path, cli.STR.file1fmt),
        (ns(file_2_path=None, file_2_format=None), cli.STR.file2path, cli.STR.file2fmt),
        (ns(input_file=None, input_format=None), cli.STR.infile, cli.STR.infmt),
        (ns(output_file=None, output_format=None), cli.STR.outfile, cli.STR.outfmt),
        (ns(values_file=None, values_format=None), cli.STR.valsfile, cli.STR.valsfmt),
    ],
)
def test__set_formats_fail(capsys, vals):
    # When reading/writing from/to stdin/stdout, the data format must be specified, since there is
    # no filename to deduce it from.
    args, file_arg, format_arg = vals
    with raises(SystemExit):
        cli._check_file_vs_format(file_arg=file_arg, format_arg=format_arg, args=args)
    assert (
        "Specify %s when %s is not specified" % (cli._arg2sw(format_arg), cli._arg2sw(file_arg))
        in capsys.readouterr().err
    )


def test__set_formats_pass_explicit():
    # Accept explcitly-specified format, whatever it is.
    fmt = "jpg"
    args = cli._check_file_vs_format(
        file_arg=cli.STR.infile,
        format_arg=cli.STR.infmt,
        args=ns(input_file="/path/to/input.txt", input_format=fmt),
    )
    assert args.input_format == "jpg"


@pytest.mark.parametrize("fmt", vars(FORMAT).keys())
def test__set_formats_pass_implicit(fmt):
    # The format is correctly deduced for a file with a known extension.
    args = cli._check_file_vs_format(
        file_arg=cli.STR.infile,
        format_arg=cli.STR.infmt,
        args=ns(input_file=f"/path/to/input.{fmt}", input_format=None),
    )
    assert args.input_format == vars(FORMAT)[fmt]


# Helper functions


def submodes(parser: Parser) -> List[str]:
    # Return submodes (named subparsers) belonging to the given parser.
    if subparsers := parser._subparsers:
        if action := subparsers._actions[1]:
            if choices := action.choices:
                submodes = choices.keys()  # type: ignore
                return list(submodes)
    return []


@fixture
def subparsers():
    # Create and return a subparsers test object.
    return Parser().add_subparsers()
