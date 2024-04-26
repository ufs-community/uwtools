# pylint: disable=missing-function-docstring,protected-access

from datetime import datetime as dt
from unittest.mock import patch

import iotaa

from uwtools.api import ungrib
from uwtools.drivers import support
from uwtools.utils import api


def test_api_ungrib_execute():
    kwargs = {
        "batch": True,
        "config": "/some/config",
        "cycle": dt.now(),
        "dry_run": True,
        "graph_file": "/some/g.dot",
        "stdin_ok": True,
        "task": "foo",
    }
    with patch.object(api, "_execute") as _execute:
        ungrib.execute(**kwargs)
        _execute.assert_called_once_with(driver_class=ungrib._Driver, **kwargs)


def test_api_ungrib_graph():
    assert ungrib.graph is support.graph


def test_api_ungrib_tasks():
    with patch.object(iotaa, "tasknames") as tasknames:
        ungrib.tasks()
        tasknames.assert_called_once_with(ungrib._Driver)
