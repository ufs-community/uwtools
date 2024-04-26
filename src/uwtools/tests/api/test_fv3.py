# pylint: disable=missing-function-docstring,protected-access

from datetime import datetime as dt
from unittest.mock import patch

import iotaa

from uwtools.api import fv3
from uwtools.drivers import support
from uwtools.utils import api


def test_api_fv3_execute():
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
        fv3.execute(**kwargs)
        _execute.assert_called_once_with(driver_class=fv3._Driver, **kwargs)


def test_api_fv3_graph():
    assert fv3.graph is support.graph


def test_api_fv3_tasks():
    with patch.object(iotaa, "tasknames") as tasknames:
        fv3.tasks()
        tasknames.assert_called_once_with(fv3._Driver)
