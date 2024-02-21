# pylint: disable=missing-function-docstring

from unittest.mock import patch

from iotaa import external, task, tasks

from uwtools.api import sfc_climo_gen


def test_execute():
    args: dict = {
        "config_file": "config.yaml",
        "batch": False,
        "dry_run": True,
    }
    with patch.object(sfc_climo_gen, "SfcClimoGen") as SfcClimoGen:
        assert sfc_climo_gen.execute(**args, task="foo") is True
    SfcClimoGen.assert_called_once_with(**args)
    SfcClimoGen().foo.assert_called_once_with()


def test_tasks():
    @external
    def t1():
        "@external t1"

    @task
    def t2():
        "@task t2"

    @tasks
    def t3():
        "@tasks t3"

    with patch.object(sfc_climo_gen, "SfcClimoGen") as SfcClimoGen:
        SfcClimoGen.t1 = t1
        SfcClimoGen.t2 = t2
        SfcClimoGen.t3 = t3
        assert sfc_climo_gen.tasks() == {"t2": "@task t2", "t3": "@tasks t3", "t1": "@external t1"}
