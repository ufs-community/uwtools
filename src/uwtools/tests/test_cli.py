# pylint: disable=missing-function-docstring

from types import SimpleNamespace as ns
from unittest.mock import DEFAULT as D
from unittest.mock import patch

import pytest
from pytest import raises

from uwtools import cli


def test_dict_from_key_eq_val_strings():
    assert not cli.dict_from_key_eq_val_strings([])
    assert cli.dict_from_key_eq_val_strings(["a=1", "b=2"]) == {"a": "1", "b": "2"}


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
