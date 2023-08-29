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
from uwtools.tests.support import logged
from uwtools.utils.file import FORMAT

# Test functions


def test__abort(capsys):
    msg = "Aborting..."
    with raises(SystemExit):
        cli._abort(msg)
    assert msg in capsys.readouterr().err


def test__add_subparser_config(subparsers):
    cli._add_subparser_config(subparsers)
    assert submodes(subparsers.choices["config"]) == ["compare", "realize", "translate", "validate"]


def test__add_subparser_config_compare(subparsers):
    cli._add_subparser_config_compare(subparsers)
    assert subparsers.choices["compare"]


def test__add_subparser_config_realize(subparsers):
    cli._add_subparser_config_realize(subparsers)
    assert subparsers.choices["realize"]


def test__add_subparser_config_translate(subparsers):
    cli._add_subparser_config_translate(subparsers)
    assert subparsers.choices["translate"]


def test__add_subparser_config_validate(subparsers):
    cli._add_subparser_config_validate(subparsers)
    assert subparsers.choices["validate"]


def test__add_subparser_forecast(subparsers):
    cli._add_subparser_forecast(subparsers)
    assert submodes(subparsers.choices["forecast"]) == ["run"]


def test__add_subparser_forecast_run(subparsers):
    cli._add_subparser_forecast_run(subparsers)
    assert subparsers.choices["run"]


def test__add_subparser_template(subparsers):
    cli._add_subparser_template(subparsers)
    assert submodes(subparsers.choices["template"]) == ["render"]


def test__add_subparser_template_render(subparsers):
    cli._add_subparser_template_render(subparsers)
    assert subparsers.choices["render"]


def test__check_args_fail_quiet_verbose(capsys):
    logging.getLogger().setLevel(logging.INFO)
    args = ns(quiet=True, verbose=True)
    with raises(SystemExit):
        cli._check_args(args)
    assert "Specify at most one of --quiet, --verbose" in capsys.readouterr().err


def test__check_args_fail_values_file_no_value_format(capsys):
    logging.getLogger().setLevel(logging.INFO)
    args = ns(values_file="foo")
    with raises(SystemExit):
        cli._check_args(args)
    assert "Specify --values-format with --values-file" in capsys.readouterr().err


def test__check_args_ok():
    args = ns(foo=88)
    assert cli._check_args(args) == args


def test__dict_from_key_eq_val_strings():
    assert not cli._dict_from_key_eq_val_strings([])
    assert cli._dict_from_key_eq_val_strings(["a=1", "b=2"]) == {"a": "1", "b": "2"}


@pytest.mark.parametrize(
    "params",
    [
        ("compare", "_dispatch_config_compare"),
        ("realize", "_dispatch_config_realize"),
        ("translate", "_dispatch_config_translate"),
        ("validate", "_dispatch_config_validate"),
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


@pytest.mark.parametrize("params", [("run", "_dispatch_forecast_run")])
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


@pytest.mark.parametrize("params", [("render", "_dispatch_template_render")])
def test__dispatch_template(params):
    submode, funcname = params
    args = ns(submode=submode)
    with patch.object(cli, funcname) as m:
        cli._dispatch_template(args)
    assert m.called_once_with(args)


def test__dispatch_template_render_yaml(caplog):
    logging.getLogger().setLevel(logging.DEBUG)
    args = ns(
        input_file=1,
        output_file=2,
        values_file=3,
        values_format=4,
        key_eq_val_pairs=["foo=88", "bar=99"],
        values_needed=6,
        dry_run=7,
    )
    with patch.object(cli.uwtools.config.templater, "render") as m:
        with patch.object(cli.sys, "argv", ["foo", "--bar", "88"]):
            cli._dispatch_template_render(args)
    assert m.called_once_with(args)
    assert logged(caplog, "Command: foo --bar 88")


@pytest.mark.parametrize("params", [(False, 1, False, True), (True, 0, True, False)])
def test_main_fail(params):
    fnretval, status, quiet, verbose = params
    with patch.multiple(
        cli, _check_args=D, _parse_args=D, _dispatch_config=D, setup_logging=D
    ) as mocks:
        args = ns(mode="config", quiet=quiet, verbose=verbose)
        mocks["_parse_args"].return_value = args
        mocks["_check_args"].return_value = mocks["_parse_args"]()
        mocks["_dispatch_config"].return_value = fnretval
        with raises(SystemExit) as e:
            cli.main()
        assert e.value.code == status
        mocks["_dispatch_config"].assert_called_once_with(args)
        mocks["_check_args"].assert_called_once_with(args)
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


# Helper functions


@fixture
def subparsers():
    # Create and return a subparsers test object.
    return Parser().add_subparsers()


def submodes(parser: Parser) -> List[str]:
    # Return submodes (named subparsers) belonging to the given parser.
    if subparsers := parser._subparsers:
        if action := subparsers._actions[1]:
            if choices := action.choices:
                submodes = choices.keys()  # type: ignore
                return list(submodes)
    return []
