# pylint: disable=missing-function-docstring,protected-access

from datetime import datetime as dt
from unittest.mock import patch

import iotaa

from uwtools.api import mpas_init
from uwtools.drivers import support
from uwtools.utils import api


def test_api_mpas_init_execute():
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
        mpas_init.execute(**kwargs)
        _execute.assert_called_once_with(driver_class=mpas_init._Driver, **kwargs)


def test_api_mpas_init_graph():
    assert mpas_init.graph is support.graph


def test_api_mpas_init_tasks():
    with patch.object(iotaa, "tasknames") as tasknames:
        mpas_init.tasks()
        tasknames.assert_called_once_with(mpas_init._Driver)
