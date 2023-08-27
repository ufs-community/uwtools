# pylint: disable=missing-function-docstring,protected-access,redefined-outer-name

from argparse import ArgumentParser as Parser
from types import SimpleNamespace as ns
from typing import List
from unittest.mock import DEFAULT as D
from unittest.mock import patch

import pytest
from pytest import fixture, raises

from uwtools import cli

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
    return Parser().add_subparsers()


def submodes(subparser: Parser) -> List[str]:
    if subparsers := subparser._subparsers:
        if action := subparsers._actions[1]:
            if choices := action.choices:
                submodes = choices.keys()  # type: ignore
                return list(submodes)
    return []
