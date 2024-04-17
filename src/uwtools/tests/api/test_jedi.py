# pylint: disable=missing-function-docstring,protected-access

import datetime as dt
from pathlib import Path
from unittest.mock import patch

from uwtools.api import jedi


def test_execute(tmp_path):
    dot = tmp_path / "graph.dot"
    args: dict = {
        "cycle": dt.datetime.now(),
        "config": Path("config.yaml"),
        "batch": False,
        "dry_run": True,
        "graph_file": dot,
    }
    with patch.object(jedi, "_JEDI") as JEDI:
        assert jedi.execute(**args, task="foo") is True
    del args["graph_file"]
    JEDI.assert_called_once_with(**args)
    JEDI().foo.assert_called_once_with()


def test_graph():
    with patch.object(jedi._support, "graph") as graph:
        jedi.graph()
    graph.assert_called_once_with()


def test_tasks():
    with patch.object(jedi._support, "tasks") as _tasks:
        jedi.tasks()
    _tasks.assert_called_once_with(jedi._JEDI)
