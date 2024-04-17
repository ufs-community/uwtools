# pylint: disable=missing-function-docstring

from pathlib import Path

import pytest
from pytest import raises

from uwtools.exceptions import UWError
from uwtools.utils import api


@pytest.mark.parametrize("val", [Path("/some/path"), {"foo": 88}])
def test_ensure_data_source_passthrough(val):
    assert api.ensure_data_source(data_source=val, stdin_ok=False) == val


def test_ensure_data_source_stdin_not_ok():
    with raises(UWError) as e:
        api.ensure_data_source(data_source=None, stdin_ok=False)
    assert str(e.value) == "Set stdin_ok=True to permit read from stdin"


def test_ensure_data_source_stdin_ok():
    assert api.ensure_data_source(data_source=None, stdin_ok=True) is None


def test_ensure_data_source_str_to_path():
    val = "/some/path"
    result = api.ensure_data_source(data_source=val, stdin_ok=False)
    assert isinstance(result, Path)
    assert result == Path(val)


@pytest.mark.parametrize("val", [Path("/some/path"), {"foo": 88}])
def test_str2path_passthrough(val):
    assert api.str2path(val) == val


def test_str2path_convert():
    val = "/some/path"
    result = api.str2path(val)
    assert isinstance(result, Path)
    assert result == Path(val)
