# pylint: disable=missing-function-docstring,protected-access,redefined-outer-name

import datetime as dt
from pathlib import Path
from unittest.mock import patch

from pytest import fixture, mark, raises

from uwtools.exceptions import UWError
from uwtools.tests.drivers.test_driver import ConcreteDriverCycleLeadtimeBased as TestDriverCL
from uwtools.tests.drivers.test_driver import ConcreteDriverTimeInvariant as TestDriver
from uwtools.utils import api


@fixture
def execute_kwargs():
    return {
        "task": "atask",
        "config": "/some/config",
        "batch": True,
        "dry_run": False,
        "graph_file": "/path/to/g.dot",
        "key_path": None,
        "stdin_ok": True,
    }


@mark.parametrize("val", [Path("/some/path"), {"foo": 88}])
def test_ensure_data_source_passthrough(val):
    assert api.ensure_data_source(data_source=val, stdin_ok=False) == val


def test_ensure_data_source_stdin_not_ok():
    with raises(UWError) as e:
        api.ensure_data_source(data_source=None, stdin_ok=False)
    assert str(e.value) == "Set stdin_ok=True to permit read from stdin"


def test_ensure_data_source_stdin_ok():
    assert api.ensure_data_source(data_source=None, stdin_ok=True) is None


def test_make_execute(execute_kwargs):
    func = api.make_execute(driver_class=TestDriver, with_cycle=False)
    assert func.__name__ == "execute"
    assert func.__doc__ is not None
    assert ":param cycle:" not in func.__doc__
    assert ":param driver_class:" not in func.__doc__
    assert ":param task:" in func.__doc__
    with patch.object(api, "_execute", return_value=True) as _execute:
        assert func(**execute_kwargs) is True
        _execute.assert_called_once_with(
            driver_class=TestDriver, cycle=None, leadtime=None, **execute_kwargs
        )


def test_make_execute_cycle(execute_kwargs):
    execute_kwargs["cycle"] = dt.datetime.now()
    func = api.make_execute(driver_class=TestDriver, with_cycle=True)
    assert func.__name__ == "execute"
    assert func.__doc__ is not None
    assert ":param cycle:" in func.__doc__
    assert ":param driver_class:" not in func.__doc__
    assert ":param task:" in func.__doc__
    with patch.object(api, "_execute", return_value=True) as _execute:
        assert func(**execute_kwargs) is True
        _execute.assert_called_once_with(driver_class=TestDriver, leadtime=None, **execute_kwargs)


def test_make_execute_cycle_leadtime(execute_kwargs):
    execute_kwargs["cycle"] = dt.datetime.now()
    execute_kwargs["leadtime"] = dt.timedelta(hours=24)
    func = api.make_execute(driver_class=TestDriver, with_cycle=True, with_leadtime=True)
    assert func.__name__ == "execute"
    assert func.__doc__ is not None
    assert ":param cycle:" in func.__doc__
    assert ":param leadtime:" in func.__doc__
    assert ":param driver_class:" not in func.__doc__
    assert ":param task:" in func.__doc__
    with patch.object(api, "_execute", return_value=True) as _execute:
        assert func(**execute_kwargs) is True
        _execute.assert_called_once_with(driver_class=TestDriver, **execute_kwargs)


def test_make_execute_leadtime_no_cycle_error(execute_kwargs):
    execute_kwargs["leadtime"] = dt.timedelta(hours=24)
    with raises(UWError) as e:
        api.make_execute(driver_class=TestDriver, with_leadtime=True)
    assert "When leadtime is specified, cycle is required" in str(e)


@mark.parametrize("hours", [0, 24, 168])
def test__execute(execute_kwargs, hours, tmp_path):
    graph_file = tmp_path / "g.dot"
    kwargs = {
        **execute_kwargs,
        "driver_class": TestDriverCL,
        "config": {"concrete": {"some": "config"}},
        "cycle": dt.datetime.now(),
        "leadtime": dt.timedelta(hours=hours),
        "graph_file": graph_file,
    }
    assert not graph_file.is_file()
    assert api._execute(**kwargs) is True
    assert graph_file.is_file()
