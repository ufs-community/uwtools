# pylint: disable=missing-function-docstring,protected-access,redefined-outer-name
"""
Tests for uwtools.drivers.driver module.
"""
import json
from pathlib import Path
from textwrap import dedent
from typing import Any, Dict
from unittest.mock import Mock, PropertyMock, patch

import pytest
import yaml
from pytest import fixture

from uwtools.config.formats.yaml import YAMLConfig
from uwtools.drivers import driver

# Helpers


class ConcreteDriver(driver.Driver):
    """
    Driver subclass for testing purposes.
    """

    def provisioned_run_directory(self):
        pass

    @property
    def _driver_config(self) -> Dict[str, Any]:
        return self._config.data

    @property
    def _driver_name(self) -> str:
        return "concrete"

    @property
    def _resources(self) -> Dict[str, Any]:
        return {
            "account": "me",
            "scheduler": "slurm",
            "walltime": "01:10:00",
        }

    def _taskname(self, suffix: str) -> str:
        return "concrete"

    def _validate(self) -> None:
        pass


def write(path, s):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(s, f)
        return path


# Fixtures


@fixture
def a_driver(tmp_path):
    cf = write(
        tmp_path / "good.yaml",
        {
            "base_file": str(write(tmp_path / "base.yaml", {"a": 11, "b": 22})),
            "execution": {"executable": "qux", "mpiargs": ["bar", "baz"], "mpicmd": "foo"},
            "update_values": {"a": 33},
            "run_dir": "/path/to/dir",
        },
    )
    return ConcreteDriver(config=cf, dry_run=True, batch=True)


# Tests


def test_Driver(a_driver):
    assert Path(a_driver._config["base_file"]).name == "base.yaml"
    assert a_driver._dry_run is True
    assert a_driver._batch is True


@pytest.mark.parametrize(
    "base_file,update_values,expected",
    [
        (False, False, {}),
        (False, True, {"a": 33}),
        (True, False, {"a": 11, "b": 22}),
        (True, True, {"a": 33, "b": 22}),
    ],
)
def test_Driver__create_user_updated_config_base_file(
    base_file, a_driver, expected, tmp_path, update_values
):
    path = tmp_path / "updated.yaml"
    cv = a_driver._config
    if not base_file:
        del cv["base_file"]
    if not update_values:
        del cv["update_values"]
    ConcreteDriver._create_user_updated_config(config_class=YAMLConfig, config_values=cv, path=path)
    with open(path, "r", encoding="utf-8") as f:
        updated = yaml.safe_load(f)
    assert updated == expected


def test_Driver__runcmd(a_driver):
    assert a_driver._runcmd == "foo bar baz qux"


def test_Driver__runscript(a_driver):
    expected = """
    #!/bin/bash

    #DIR --d1
    #DIR --d2

    cmd1
    cmd2

    export VAR1=1
    export VAR2=2

    foo
    bar
    """
    scheduler = Mock(directives=["#DIR --d1", "#DIR --d2"])
    assert (
        a_driver._runscript(
            execution=["foo", "bar"],
            envcmds=["cmd1", "cmd2"],
            envvars={"VAR1": 1, "VAR2": 2},
            scheduler=scheduler,
        )
        == dedent(expected).strip()
    )


def test_Driver__runscript_execution_only(a_driver):
    expected = """
    #!/bin/bash

    foo
    bar
    """
    assert a_driver._runscript(execution=["foo", "bar"]) == dedent(expected).strip()


def test_Driver__run_via_batch_submission(a_driver):
    runscript = a_driver._runscript_path
    with patch.object(a_driver, "provisioned_run_directory") as prd:
        with patch.object(ConcreteDriver, "_scheduler", new_callable=PropertyMock) as scheduler:
            a_driver._run_via_batch_submission()
            scheduler().submit_job.assert_called_once_with(
                runscript=runscript, submit_file=Path(f"{runscript}.submit")
            )
        prd.assert_called_once_with()


def test_Driver__run_via_local_execution(a_driver):
    with patch.object(a_driver, "provisioned_run_directory") as prd:
        with patch.object(driver, "execute") as execute:
            a_driver._run_via_local_execution()
            execute.assert_called_once_with(
                cmd="{x} >{x}.out 2>&1".format(x=a_driver._runscript_path),
                cwd=a_driver._rundir,
                log_output=True,
            )
        prd.assert_called_once_with()


def test_Driver__scheduler(a_driver):
    with patch.object(driver, "JobScheduler") as JobScheduler:
        scheduler = JobScheduler.get_scheduler()
        assert a_driver._scheduler == scheduler
        JobScheduler.get_scheduler.assert_called_with(a_driver._resources)
