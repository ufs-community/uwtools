# pylint: disable=missing-function-docstring

from unittest.mock import patch

from uwtools.api import sfc_climo_gen


def test_execute(tmp_path):
    dot = tmp_path / "graph.dot"
    args: dict = {
        "config_file": "config.yaml",
        "batch": False,
        "dry_run": True,
        "graph_file": dot,
    }
    with patch.object(sfc_climo_gen, "SfcClimoGen") as SfcClimoGen:
        assert sfc_climo_gen.execute(**args, task="foo") is True
    del args["graph_file"]
    SfcClimoGen.assert_called_once_with(**args)
    SfcClimoGen().foo.assert_called_once_with()


def test_graph():
    with patch.object(sfc_climo_gen.support, "graph") as graph:
        sfc_climo_gen.graph()
    graph.assert_called_once_with()


def test_tasks():
    with patch.object(sfc_climo_gen.support, "tasks") as _tasks:
        sfc_climo_gen.tasks()
    _tasks.assert_called_once_with(sfc_climo_gen.SfcClimoGen)
