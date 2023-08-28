# pylint: disable=missing-function-docstring,protected-access,redefined-outer-name

import logging
from argparse import ArgumentParser as Parser
from types import SimpleNamespace as ns
from typing import List
from unittest.mock import DEFAULT as D
from unittest.mock import patch

import pytest
from pytest import fixture, raises

from uwtools import cli
from uwtools.tests.support import logged

# Test functions


def test_add_subparser_config(subparsers):
    cli.add_subparser_config(subparsers)
    assert submodes(subparsers.choices["config"]) == ["compare", "realize", "translate", "validate"]


def test_add_subparser_config_compare(subparsers):
    cli.add_subparser_config_compare(subparsers)
    assert subparsers.choices["compare"]


def test_add_subparser_config_realize(subparsers):
    cli.add_subparser_config_realize(subparsers)
    assert subparsers.choices["realize"]


def test_add_subparser_config_translate(subparsers):
    cli.add_subparser_config_translate(subparsers)
    assert subparsers.choices["translate"]


def test_add_subparser_config_validate(subparsers):
    cli.add_subparser_config_validate(subparsers)
    assert subparsers.choices["validate"]


def test_add_subparser_forecast(subparsers):
    cli.add_subparser_forecast(subparsers)
    assert submodes(subparsers.choices["forecast"]) == ["run"]


def test_add_subparser_forecast_run(subparsers):
    cli.add_subparser_forecast_run(subparsers)
    assert subparsers.choices["run"]


def test_add_subparser_template(subparsers):
    cli.add_subparser_template(subparsers)
    assert submodes(subparsers.choices["template"]) == ["render"]


def test_add_subparser_template_render(subparsers):
    cli.add_subparser_template_render(subparsers)
    assert subparsers.choices["render"]


@pytest.mark.parametrize(
    "params",
    [
        ("compare", "dispatch_config_compare"),
        ("realize", "dispatch_config_realize"),
        ("translate", "dispatch_config_translate"),
        ("validate", "dispatch_config_validate"),
    ],
)
def test_dispatch_config(params):
    submode, funcname = params
    args = ns(submode=submode)
    with patch.object(cli, funcname) as m:
        cli.dispatch_config(args)  # type: ignore
    assert m.called_once_with(args)


def test_dispatch_config_compare():
    args = ns(file_1_path=1, file_1_format=2, file_2_path=3, file_2_format=4)
    with patch.object(cli.uwtools.config.core, "compare_configs") as m:
        cli.dispatch_config_compare(args)  # type: ignore
    assert m.called_once_with(args)


def test_dispatch_config_realize():
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
        cli.dispatch_config_realize(args)  # type: ignore
    assert m.called_once_with(args)


def test_dispatch_config_translate_arparse_to_jinja2():
    args = ns(
        input_file=1, input_format="atparse", output_file=3, output_format="jinja2", dry_run=5
    )
    with patch.object(cli.uwtools.config.atparse_to_jinja2, "convert") as m:
        cli.dispatch_config_translate(args)  # type: ignore
    assert m.called_once_with(args)


def test_dispath_config_translate_unsupported():
    args = ns(input_file=1, input_format="jpg", output_file=3, output_format="png", dry_run=5)
    assert cli.dispatch_config_translate(args) is False  # type: ignore


def test_dispatch_config_validate_yaml():
    args = ns(input_file=1, input_format="yaml", schema_file=3)
    with patch.object(cli.uwtools.config.validator, "validate_yaml") as m:
        cli.dispatch_config_validate(args)  # type: ignore
    assert m.called_once_with(args)


def test_dispath_config_validate_unsupported():
    args = ns(input_file=1, input_format="jpg", schema_file=3)
    assert cli.dispatch_config_validate(args) is False  # type: ignore


@pytest.mark.parametrize("params", [("run", "dispatch_forecast_run")])
def test_dispatch_forecast(params):
    submode, funcname = params
    args = ns(submode=submode)
    with patch.object(cli, funcname) as m:
        cli.dispatch_forecast(args)  # type: ignore
    assert m.called_once_with(args)


def test_dispatch_forecast_run():
    args = ns(config_file=1, forecast_model="foo")
    with patch.object(cli.uwtools.drivers.forecast, "FooForecast", create=True) as m:
        CLASSES = {"foo": getattr(cli.uwtools.drivers.forecast, "FooForecast")}
        with patch.object(cli.uwtools.drivers.forecast, "CLASSES", new=CLASSES):
            cli.dispatch_forecast_run(args)  # type: ignore
    assert m.called_once_with(args)
    m().run.assert_called_once_with()


@pytest.mark.parametrize("params", [("render", "dispatch_template_render")])
def test_dispatch_template(params):
    submode, funcname = params
    args = ns(submode=submode)
    with patch.object(cli, funcname) as m:
        cli.dispatch_template(args)  # type: ignore
    assert m.called_once_with(args)


def test_dispatch_template_render_yaml(caplog):
    logging.getLogger().setLevel(logging.DEBUG)
    args = ns(
        input_file=1,
        output_file=2,
        values_file=3,
        key_eq_val_pairs=["foo=88", "bar=99"],
        values_needed=5,
        dry_run=6,
    )
    with patch.object(cli.uwtools.config.templater, "render") as m:
        with patch.object(cli.sys, "argv", ["foo", "--bar", "88"]):
            cli.dispatch_template_render(args)  # type: ignore
    assert m.called_once_with(args)
    assert logged(caplog, "Command: foo --bar 88")


@pytest.mark.parametrize("params", [(False, 1, False, True), (True, 0, True, False)])
def test_main_fail(params):
    fnretval, status, quiet, verbose = params
    with patch.multiple(
        cli, check_args=D, parse_args=D, dispatch_config=D, setup_logging=D
    ) as mocks:
        args = ns(mode="config", quiet=quiet, verbose=verbose)
        mocks["parse_args"].return_value = args
        mocks["check_args"].return_value = mocks["parse_args"]()
        mocks["dispatch_config"].return_value = fnretval
        with raises(SystemExit) as e:
            cli.main()
        assert e.value.code == status
        mocks["dispatch_config"].assert_called_once_with(args)
        mocks["check_args"].assert_called_once_with(args)
        mocks["setup_logging"].assert_called_once_with(quiet=quiet, verbose=verbose)


def test_dict_from_key_eq_val_strings():
    assert not cli.dict_from_key_eq_val_strings([])
    assert cli.dict_from_key_eq_val_strings(["a=1", "b=2"]) == {"a": "1", "b": "2"}


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
