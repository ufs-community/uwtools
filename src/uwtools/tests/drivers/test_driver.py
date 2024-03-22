# pylint: disable=missing-function-docstring,protected-access,redefined-outer-name
"""
Tests for uwtools.drivers.driver module.
"""
import json
from pathlib import Path
from textwrap import dedent
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
    def _driver_name(self) -> str:
        return "concrete"

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
def driverobj(tmp_path):
    cf = write(
        tmp_path / "good.yaml",
        {
            "concrete": {
                "base_file": str(write(tmp_path / "base.yaml", {"a": 11, "b": 22})),
                "execution": {
                    "batchargs": {
                        "export": "NONE",
                        "nodes": 1,
                        "stdout": "/path/to/file",
                        "walltime": "00:05:00",
                    },
                    "executable": "qux",
                    "mpiargs": ["bar", "baz"],
                    "mpicmd": "foo",
                },
                "run_dir": "/path/to/dir",
                "update_values": {"a": 33},
            },
            "platform": {
                "account": "me",
                "scheduler": "slurm",
            },
        },
    )
    return ConcreteDriver(config=cf, dry_run=True, batch=True)


# Tests


def test_Driver(driverobj):
    assert Path(driverobj._driver_config["base_file"]).name == "base.yaml"
    assert driverobj._dry_run is True
    assert driverobj._batch is True


# Tests for workflow methods


@pytest.mark.parametrize("batch", [True, False])
def test_Driver_run(driverobj, batch):
    driverobj._batch = batch
    with patch.object(driverobj, "_run_via_batch_submission") as rvbs:
        with patch.object(driverobj, "_run_via_local_execution") as rvle:
            driverobj.run()
        if batch:
            rvbs.assert_called_once_with()
            rvle.assert_not_called()
        else:
            rvbs.assert_not_called()
            rvle.assert_called_once_with()


def test_Driver__run_via_batch_submission(driverobj):
    runscript = driverobj._runscript_path
    with patch.object(driverobj, "provisioned_run_directory") as prd:
        with patch.object(ConcreteDriver, "_scheduler", new_callable=PropertyMock) as scheduler:
            driverobj._run_via_batch_submission()
            scheduler().submit_job.assert_called_once_with(
                runscript=runscript, submit_file=Path(f"{runscript}.submit")
            )
        prd.assert_called_once_with()


def test_Driver__run_via_local_execution(driverobj):
    with patch.object(driverobj, "provisioned_run_directory") as prd:
        with patch.object(driver, "execute") as execute:
            driverobj._run_via_local_execution()
            execute.assert_called_once_with(
                cmd="{x} >{x}.out 2>&1".format(x=driverobj._runscript_path),
                cwd=driverobj._rundir,
                log_output=True,
            )
        prd.assert_called_once_with()


# Tests for private helper methods


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
    base_file, driverobj, expected, tmp_path, update_values
):
    path = tmp_path / "updated.yaml"
    dc = driverobj._driver_config
    if not base_file:
        del dc["base_file"]
    if not update_values:
        del dc["update_values"]
    ConcreteDriver._create_user_updated_config(config_class=YAMLConfig, config_values=dc, path=path)
    with open(path, "r", encoding="utf-8") as f:
        updated = yaml.safe_load(f)
    assert updated == expected


def test_Driver__driver_config(driverobj):
    assert set(driverobj._driver_config.keys()) == {
        "base_file",
        "execution",
        "run_dir",
        "update_values",
    }


def test_Driver__resources(driverobj):
    account = "me"
    scheduler = "slurm"
    walltime = "00:05:00"
    driverobj._driver_config["execution"].update({"batchargs": {"walltime": walltime}})
    driverobj._config["platform"] = {"account": account, "scheduler": scheduler}
    assert driverobj._resources == {
        "account": account,
        "rundir": driverobj._rundir,
        "scheduler": scheduler,
        "walltime": walltime,
    }


def test_Driver__runcmd(driverobj):
    assert driverobj._runcmd == "foo bar baz qux"


def test_Driver__runscript(driverobj):
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
        driverobj._runscript(
            execution=["foo", "bar"],
            envcmds=["cmd1", "cmd2"],
            envvars={"VAR1": 1, "VAR2": 2},
            scheduler=scheduler,
        )
        == dedent(expected).strip()
    )


def test_Driver__runscript_execution_only(driverobj):
    expected = """
    #!/bin/bash

    foo
    bar
    """
    assert driverobj._runscript(execution=["foo", "bar"]) == dedent(expected).strip()


def test_Driver__rundir(driverobj):
    assert driverobj._rundir == Path("/path/to/dir")


def test_Driver__runscript_path(driverobj):
    assert driverobj._runscript_path == Path("/path/to/dir/runscript.concrete")


def test_Driver__scheduler(driverobj):
    with patch.object(driver, "JobScheduler") as JobScheduler:
        scheduler = JobScheduler.get_scheduler()
        assert driverobj._scheduler == scheduler
        JobScheduler.get_scheduler.assert_called_with(driverobj._resources)


def test_Driver__validate(driverobj):
    with patch.object(driverobj, "_validate", driver.Driver._validate):
        with patch.object(driver, "validate_internal") as validate_internal:
            driverobj._validate(driverobj)
        assert validate_internal.call_args_list[0].kwargs == {
            "schema_name": "concrete",
            "config": driverobj._config,
        }
        assert validate_internal.call_args_list[1].kwargs == {
            "schema_name": "platform",
            "config": driverobj._config,
        }


def test_Driver__write_runscript(driverobj, tmp_path):
    path = tmp_path / "runscript"
    driverobj._write_runscript(path=path, envvars={"FOO": "bar", "BAZ": "qux"})
    expected = """
    #!/bin/bash

    #SBATCH --account=me
    #SBATCH --chdir=/path/to/dir
    #SBATCH --export=NONE
    #SBATCH --nodes=1
    #SBATCH --output=/path/to/file
    #SBATCH --time=00:05:00

    export FOO=bar
    export BAZ=qux

    time foo bar baz qux
    test $? -eq 0 && touch /path/to/dir/done
    """
    with open(path, "r", encoding="utf-8") as f:
        actual = f.read()
    assert actual.strip() == dedent(expected).strip()
