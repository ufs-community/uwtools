# pylint: disable=missing-function-docstring,protected-access,redefined-outer-name

from datetime import datetime as dt
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml
from pytest import fixture, raises

from uwtools.exceptions import UWError
from uwtools.tests.drivers.test_driver import ConcreteDriver
from uwtools.utils import api


@fixture
def execute_kwargs():
    return {
        "task": "atask",
        "config": "/some/config",
        "batch": True,
        "dry_run": True,
        "graph_file": "/path/to/g.dot",
        "stdin_ok": True,
    }


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


def test_make_execute(execute_kwargs):
    func = api.make_execute(driver_class=ConcreteDriver, with_cycle=False)
    assert func.__name__ == "execute"
    assert func.__doc__ is not None
    assert ":param cycle:" not in func.__doc__
    assert ":param driver_class:" not in func.__doc__
    assert ":param task:" in func.__doc__
    with patch.object(api, "_execute", return_value=True) as _execute:
        assert func(**execute_kwargs) is True
        _execute.assert_called_once_with(driver_class=ConcreteDriver, cycle=None, **execute_kwargs)


def test_make_execute_cycle(execute_kwargs):
    execute_kwargs["cycle"] = dt.now()
    func = api.make_execute(driver_class=ConcreteDriver, with_cycle=True)
    assert func.__name__ == "execute"
    assert func.__doc__ is not None
    assert ":param cycle:" in func.__doc__
    assert ":param driver_class:" not in func.__doc__
    assert ":param task:" in func.__doc__
    with patch.object(api, "_execute", return_value=True) as _execute:
        assert func(**execute_kwargs) is True
        _execute.assert_called_once_with(driver_class=ConcreteDriver, **execute_kwargs)


def test_make_tasks():
    func = api.make_tasks(driver_class=ConcreteDriver)
    assert func.__name__ == "tasks"
    taskmap = func()
    assert list(taskmap.keys()) == ["atask", "run", "validate"]


@pytest.mark.parametrize("val", [Path("/some/path"), {"foo": 88}])
def test_str2path_passthrough(val):
    assert api.str2path(val) == val


def test_str2path_convert():
    val = "/some/path"
    result = api.str2path(val)
    assert isinstance(result, Path)
    assert result == Path(val)


def test__execute(execute_kwargs, tmp_path):
    config = tmp_path / "config.yaml"
    with open(config, "w", encoding="utf-8") as f:
        yaml.dump({"some": "config"}, f)
    graph_file = tmp_path / "g.dot"
    kwargs = {
        **execute_kwargs,
        "driver_class": ConcreteDriver,
        "config": config,
        "cycle": dt.now(),
        "graph_file": graph_file,
    }
    assert not graph_file.is_file()
    with patch.object(ConcreteDriver, "_validate"):
        assert api._execute(**kwargs) is True
    assert graph_file.is_file()
