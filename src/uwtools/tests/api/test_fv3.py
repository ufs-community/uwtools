# pylint: disable=missing-function-docstring,protected-access

import datetime as dt
from unittest.mock import patch

from uwtools.api import fv3


def test_execute(tmp_path):
    dot = tmp_path / "graph.dot"
    args: dict = {
        "batch": False,
        "config": "config.yaml",
        "cycle": dt.datetime.now(),
        "dry_run": True,
        "graph_file": dot,
    }
    with patch.object(fv3, "_FV3") as FV3:
        assert fv3.execute(**args, task="foo") is True
    del args["graph_file"]
    FV3.assert_called_once_with(**args)
    FV3().foo.assert_called_once_with()


def test_graph():
    with patch.object(fv3._support, "graph") as graph:
        fv3.graph()
    graph.assert_called_once_with()


def test_tasks():
    with patch.object(fv3._support, "tasks") as _tasks:
        fv3.tasks()
    _tasks.assert_called_once_with(fv3._FV3)
