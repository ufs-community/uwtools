# pylint: disable=missing-function-docstring,protected-access

import datetime as dt
from unittest.mock import patch

from iotaa import external, task, tasks

from uwtools.api import fv3


@external
def t1():
    "@external t1"


@task
def t2():
    "@task t2"


@tasks
def t3():
    "@tasks t3"


def test_execute():
    args: dict = {
        "config_file": "config.yaml",
        "cycle": dt.datetime.utcnow(),
        "batch": False,
        "dry_run": True,
    }
    with patch.object(fv3, "FV3") as FV3:
        assert fv3.execute(**args, task="foo") is True
    FV3.assert_called_once_with(**args)
    FV3().foo.assert_called_once_with()


def test_tasks():
    with patch.object(fv3, "FV3") as FV3:
        FV3.t1 = t1
        FV3.t2 = t2
        FV3.t3 = t3
        assert fv3.tasks() == {"t2": "@task t2", "t3": "@tasks t3", "t1": "@external t1"}
