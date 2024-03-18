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
from pytest import fixture, raises

from uwtools.config.formats.yaml import YAMLConfig
from uwtools.drivers import driver
from uwtools.exceptions import UWConfigError

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
def driver_bad(tmp_path):
    cf = write(tmp_path / "bad.yaml", {"base_file": 88})
    return ConcreteDriver(config_file=cf, dry_run=True, batch=True)


@fixture
def driver_good(tmp_path):
    cf = write(
        tmp_path / "good.yaml",
        {
            "base_file": str(write(tmp_path / "base.yaml", {"a": 11, "b": 22})),
            "execution": {"executable": "qux", "mpiargs": ["bar", "baz"], "mpicmd": "foo"},
            "update_values": {"a": 33},
            "run_dir": "/path/to/dir",
        },
    )
    return ConcreteDriver(config_file=cf, dry_run=True, batch=True)


@fixture
def schema(tmp_path):
    return write(
        tmp_path / "a.jsonschema",
        {
            "properties": {"base_file": {"type": "string"}, "update_values": {"type": "object"}},
            "type": "object",
        },
    )


def test_Driver(driver_good):
    assert Path(driver_good._config["base_file"]).name == "base.yaml"
    assert driver_good._dry_run is True
    assert driver_good._batch is True


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
    base_file, driver_good, expected, tmp_path, update_values
):
    path = tmp_path / "updated.yaml"
    cv = driver_good._config
    if not base_file:
        del cv["base_file"]
    if not update_values:
        del cv["update_values"]
    ConcreteDriver._create_user_updated_config(config_class=YAMLConfig, config_values=cv, path=path)
    with open(path, "r", encoding="utf-8") as f:
        updated = yaml.safe_load(f)
    assert updated == expected


def test_Driver__runcmd(driver_good):
    assert driver_good._runcmd == "foo bar baz qux"


def test_Driver__runscript(driver_good):
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
        driver_good._runscript(
            execution=["foo", "bar"],
            envcmds=["cmd1", "cmd2"],
            envvars={"VAR1": 1, "VAR2": 2},
            scheduler=scheduler,
        )
        == dedent(expected).strip()
    )


def test_Driver__runscript_execution_only(driver_good):
    expected = """
    #!/bin/bash

    foo
    bar
    """
    assert driver_good._runscript(execution=["foo", "bar"]) == dedent(expected).strip()


def test_Driver__run_via_batch_submission(driver_good):
    runscript = driver_good._runscript_path
    with patch.object(driver_good, "provisioned_run_directory") as prd:
        with patch.object(ConcreteDriver, "_scheduler", new_callable=PropertyMock) as scheduler:
            driver_good._run_via_batch_submission()
            scheduler().submit_job.assert_called_once_with(
                runscript=runscript, submit_file=Path(f"{runscript}.submit")
            )
        prd.assert_called_once_with()


def test_Driver__run_via_local_execution(driver_good):
    with patch.object(driver_good, "provisioned_run_directory") as prd:
        with patch.object(driver, "execute") as execute:
            driver_good._run_via_local_execution()
            execute.assert_called_once_with(
                cmd="{x} >{x}.out 2>&1".format(x=driver_good._runscript_path),
                cwd=driver_good._rundir,
                log_output=True,
            )
        prd.assert_called_once_with()


def test_Driver__scheduler(driver_good):
    with patch.object(driver, "JobScheduler") as JobScheduler:
        scheduler = JobScheduler.get_scheduler()
        assert driver_good._scheduler == scheduler
        JobScheduler.get_scheduler.assert_called_with(driver_good._resources)


def test_Driver__validate_one_no(driver_bad, schema):
    with patch.object(driver, "resource_path", return_value=schema.parent):
        with raises(UWConfigError) as e:
            driver_bad._validate_one(schema.stem)
    assert str(e.value) == "YAML validation errors"


def test_Driver__validate_one_ok(driver_good, schema):
    with patch.object(driver, "resource_path", return_value=schema.parent):
        driver_good._validate_one(schema.stem)
