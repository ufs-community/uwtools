# pylint: disable=missing-function-docstring,protected-access

import datetime as dt
from unittest.mock import patch

from uwtools.api import mpas_init


def test_execute(tmp_path):
    dot = tmp_path / "graph.dot"
    args: dict = {
        "config": "config.yaml",
        "cycle": dt.datetime.utcnow(),
        "batch": False,
        "dry_run": True,
        "graph_file": dot,
    }
    with patch.object(mpas_init, "_MPASInit") as SfcClimoGen:
        assert mpas_init.execute(**args, task="foo") is True
    del args["graph_file"]
    SfcClimoGen.assert_called_once_with(**args)
    SfcClimoGen().foo.assert_called_once_with()


def test_graph():
    with patch.object(mpas_init._support, "graph") as graph:
        mpas_init.graph()
    graph.assert_called_once_with()


def test_tasks():
    with patch.object(mpas_init._support, "tasks") as _tasks:
        mpas_init.tasks()
    _tasks.assert_called_once_with(mpas_init._MPASInit)