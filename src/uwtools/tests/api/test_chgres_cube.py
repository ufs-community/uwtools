# pylint: disable=missing-function-docstring,protected-access

from datetime import datetime as dt
from unittest.mock import patch

import iotaa

from uwtools.api import chgres_cube
from uwtools.drivers import support
from uwtools.utils import api


def test_api_chgres_cube_execute():
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
        chgres_cube.execute(**kwargs)
        _execute.assert_called_once_with(driver_class=chgres_cube._Driver, **kwargs)


def test_api_chgres_cube_graph():
    assert chgres_cube.graph is support.graph


def test_api_chgres_cube_tasks():
    with patch.object(iotaa, "tasknames") as tasknames:
        chgres_cube.tasks()
        tasknames.assert_called_once_with(chgres_cube._Driver)
