# pylint: disable=missing-function-docstring

from pathlib import Path

import pytest
from pytest import raises

from uwtools.exceptions import UWError
from uwtools.utils import api


@pytest.mark.parametrize("val", [Path("/some/path"), {"foo": 88}])
def test_ensure_config_passthrough(val):
    assert api.ensure_config(config=val, stdin_ok=False) == val


def test_ensure_config_stdin_not_ok():
    with raises(UWError) as e:
        api.ensure_config(config=None, stdin_ok=False)
    assert str(e.value) == "Set stdin_ok=True to enable read from stdin"


def test_ensure_config_stdin_ok():
    assert api.ensure_config(config=None, stdin_ok=True) is None


def test_ensure_config_str_to_path():
    val = "/some/path"
    assert api.ensure_config(config=val, stdin_ok=False) == Path(val)
