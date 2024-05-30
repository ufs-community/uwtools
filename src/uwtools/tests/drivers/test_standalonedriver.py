# pylint: disable=missing-function-docstring,protected-access,redefined-outer-name
"""
Tests for uwtools.drivers.driver module.
"""
import datetime as dt
import json
from pathlib import Path
from textwrap import dedent
from unittest.mock import Mock, PropertyMock, patch

import pytest
from iotaa import asset, task
from pytest import fixture, raises

from uwtools.drivers import driver
from uwtools.exceptions import UWConfigError

# Helpers


class ConcreteDriver(driver.StandaloneDriver):
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

    @task
    def atask(self):
        yield "atask"
        yield asset("atask", lambda: True)


def write(path, s):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(s, f)
        return path


# Fixtures


@fixture
def config(tmp_path):
    return {
        "concrete": {
            "base_file": str(write(tmp_path / "base.yaml", {"a": 11, "b": 22})),
            "execution": {
                "batchargs": {
                    "export": "NONE",
                    "nodes": 1,
                    "stdout": "{{ concrete.run_dir }}/out",
                    "walltime": "00:05:00",
                },
                "executable": str(tmp_path / "qux"),
                "mpiargs": ["bar", "baz"],
                "mpicmd": "foo",
            },
            "run_dir": "{{ rootdir }}/{{ cycle.strftime('%Y%m%d%H') }}/run",
            "update_values": {"a": 33},
        },
        "platform": {
            "account": "me",
            "scheduler": "slurm",
        },
        "rootdir": "/path/to",
    }


@fixture
def driverobj(config):
    return ConcreteDriver(
        config=config,
        dry_run=False,
        batch=True,
        cycle=dt.datetime(2024, 3, 22, 18),
        leadtime=dt.timedelta(hours=24),
    )


# Tests


def test_StandaloneDriver(driverobj):
    assert Path(driverobj._driver_config["base_file"]).name == "base.yaml"
    assert driverobj._batch is True


# Tests for workflow methods


@pytest.mark.parametrize("batch", [True, False])
def test_StandaloneDriver_run(batch, driverobj):
    driverobj._batch = batch
    executable = Path(driverobj._driver_config["execution"]["executable"])
    executable.touch()
    with patch.object(driverobj, "_run_via_batch_submission") as rvbs:
        with patch.object(driverobj, "_run_via_local_execution") as rvle:
            driverobj.run()
        if batch:
            rvbs.assert_called_once_with()
            rvle.assert_not_called()
        else:
            rvbs.assert_not_called()
            rvle.assert_called_once_with()


def test_StandaloneDriver__run_via_batch_submission(driverobj):
    runscript = driverobj._runscript_path
    executable = Path(driverobj._driver_config["execution"]["executable"])
    executable.touch()
    with patch.object(driverobj, "provisioned_run_directory") as prd:
        with patch.object(ConcreteDriver, "_scheduler", new_callable=PropertyMock) as scheduler:
            driverobj._run_via_batch_submission()
            scheduler().submit_job.assert_called_once_with(
                runscript=runscript, submit_file=Path(f"{runscript}.submit")
            )
        prd.assert_called_once_with()


def test_StandaloneDriver__run_via_local_execution(driverobj):
    executable = Path(driverobj._driver_config["execution"]["executable"])
    executable.touch()
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


def test_StandaloneDriver__resources_fail(driverobj):
    del driverobj._config["platform"]
    with raises(UWConfigError) as e:
        assert driverobj._resources
    assert str(e.value) == "Required 'platform' block missing in config"


def test_StandaloneDriver__resources_pass(driverobj):
    account = "me"
    scheduler = "slurm"
    walltime = "00:05:00"
    driverobj._driver_config["execution"].update({"batchargs": {"walltime": walltime}})
    assert driverobj._resources == {
        "account": account,
        "rundir": driverobj._rundir,
        "scheduler": scheduler,
        "stdout": "runscript.concrete.out",
        "walltime": walltime,
    }


def test_StandaloneDriver__runcmd(driverobj):
    executable = driverobj._driver_config["execution"]["executable"]
    assert driverobj._runcmd == f"foo bar baz {executable}"


def test_StandaloneDriver__runscript(driverobj):
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


def test_StandaloneDriver__runscript_execution_only(driverobj):
    expected = """
    #!/bin/bash

    foo
    bar
    """
    assert driverobj._runscript(execution=["foo", "bar"]) == dedent(expected).strip()


def test_StandaloneDriver__runscript_path(driverobj):
    assert driverobj._runscript_path == Path("/path/to/2024032218/run/runscript.concrete")


def test_StandaloneDriver__scheduler(driverobj):
    with patch.object(driver, "JobScheduler") as JobScheduler:
        scheduler = JobScheduler.get_scheduler()
        assert driverobj._scheduler == scheduler
        JobScheduler.get_scheduler.assert_called_with(driverobj._resources)


def test_StandaloneDriver__write_runscript(driverobj, tmp_path):
    path = tmp_path / "runscript"
    executable = driverobj._driver_config["execution"]["executable"]
    driverobj._write_runscript(path=path, envvars={"FOO": "bar", "BAZ": "qux"})
    expected = f"""
    #!/bin/bash

    #SBATCH --account=me
    #SBATCH --chdir=/path/to/2024032218/run
    #SBATCH --export=NONE
    #SBATCH --nodes=1
    #SBATCH --output=/path/to/2024032218/run/out
    #SBATCH --time=00:05:00

    export FOO=bar
    export BAZ=qux

    time foo bar baz {executable}
    test $? -eq 0 && touch runscript.concrete.done
    """
    with open(path, "r", encoding="utf-8") as f:
        actual = f.read()
    assert actual.strip() == dedent(expected).strip()
