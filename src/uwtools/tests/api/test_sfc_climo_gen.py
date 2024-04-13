# pylint: disable=missing-function-docstring,protected-access

from pathlib import Path
from unittest.mock import patch

from uwtools.api import sfc_climo_gen


def test_execute(tmp_path):
    dot = tmp_path / "graph.dot"
    kwargs: dict = {
        "batch": False,
        "config": "config.yaml",
        "dry_run": True,
        "graph_file": dot,
    }
    with patch.object(sfc_climo_gen, "_SfcClimoGen") as SfcClimoGen:
        assert sfc_climo_gen.execute(**kwargs, task="foo") is True
    del kwargs["graph_file"]
    SfcClimoGen.assert_called_once_with(**{**kwargs, "config": Path(kwargs["config"])})
    SfcClimoGen().foo.assert_called_once_with()


def test_graph():
    with patch.object(sfc_climo_gen._support, "graph") as graph:
        sfc_climo_gen.graph()
    graph.assert_called_once_with()


def test_tasks():
    with patch.object(sfc_climo_gen._support, "tasks") as _tasks:
        sfc_climo_gen.tasks()
    _tasks.assert_called_once_with(sfc_climo_gen._SfcClimoGen)
