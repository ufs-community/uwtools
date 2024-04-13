# pylint: disable=missing-function-docstring,protected-access,redefined-outer-name

from pathlib import Path
from unittest.mock import patch

from pytest import fixture

from uwtools.api import sfc_climo_gen


@fixture
def kwargs():
    return {
        "batch": False,
        "config": "config.yaml",
        "dry_run": True,
    }


def test_execute(kwargs, tmp_path):
    with patch.object(sfc_climo_gen, "_SfcClimoGen") as SfcClimoGen:
        assert (
            sfc_climo_gen.execute(**kwargs, task="foo", graph_file=tmp_path / "graph.dot") is True
        )
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
