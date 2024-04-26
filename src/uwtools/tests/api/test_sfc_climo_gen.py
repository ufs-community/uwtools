# pylint: disable=missing-function-docstring,protected-access

from unittest.mock import patch

import iotaa

from uwtools.api import sfc_climo_gen
from uwtools.drivers import support
from uwtools.utils import api


def test_api_sfc_climo_gen_execute():
    kwargs = {
        "batch": True,
        "config": "/some/config",
        "dry_run": True,
        "graph_file": "/some/g.dot",
        "stdin_ok": True,
        "task": "foo",
    }
    with patch.object(api, "_execute") as _execute:
        sfc_climo_gen.execute(**kwargs)
        _execute.assert_called_once_with(driver_class=sfc_climo_gen._Driver, cycle=None, **kwargs)


def test_api_sfc_climo_gen_graph():
    assert sfc_climo_gen.graph is support.graph


def test_api_sfc_climo_gen_tasks():
    with patch.object(iotaa, "tasknames") as tasknames:
        sfc_climo_gen.tasks()
        tasknames.assert_called_once_with(sfc_climo_gen._Driver)
