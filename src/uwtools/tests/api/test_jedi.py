# pylint: disable=missing-function-docstring,protected-access

from datetime import datetime as dt
from unittest.mock import patch

import iotaa

from uwtools.api import jedi
from uwtools.drivers import support
from uwtools.utils import api


def test_api_jedi_execute():
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
        jedi.execute(**kwargs)
        _execute.assert_called_once_with(driver_class=jedi._Driver, **kwargs)


def test_api_jedi_graph():
    assert jedi.graph is support.graph


def test_api_jedi_tasks():
    with patch.object(iotaa, "tasknames") as tasknames:
        jedi.tasks()
        tasknames.assert_called_once_with(jedi._Driver)
