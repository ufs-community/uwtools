# pylint: disable=missing-function-docstring,protected-access,redefined-outer-name
"""
Tests for uwtools.drivers.driver module.
"""
import datetime as dt
import json
import logging
from pathlib import Path
from textwrap import dedent
from unittest.mock import Mock, PropertyMock, patch

import pytest
import yaml
from iotaa import asset, task
from pytest import fixture, raises

from uwtools.config.formats.yaml import YAMLConfig
from uwtools.drivers import driver
from uwtools.exceptions import UWConfigError, UWError
from uwtools.logging import log
from uwtools.tests.support import regex_logged

# Helpers


class ConcreteAssets(driver.Assets):
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
def assetobj(config):
    return ConcreteAssets(
        config=config,
        dry_run=False,
        batch=True,
        cycle=dt.datetime(2024, 3, 22, 18),
        leadtime=dt.timedelta(hours=24),
    )


@fixture
def driverobj(config):
    return ConcreteDriver(
        config=config,
        dry_run=False,
        batch=True,
        cycle=dt.datetime(2024, 3, 22, 18),
        leadtime=dt.timedelta(hours=24),
    )


# Assets Tests


def test_Assets(assetobj):
    assert Path(assetobj._driver_config["base_file"]).name == "base.yaml"
    assert assetobj._batch is True


@pytest.mark.parametrize("hours", [0, 24, 168])
def test_Assets_cycle_leadtime_error(config, hours):
    with raises(UWError) as e:
        ConcreteAssets(config=config, leadtime=dt.timedelta(hours=hours))
    assert "When leadtime is specified, cycle is required" in str(e)


@pytest.mark.parametrize("val", (True, False))
def test_Assets_dry_run(config, val):
    with patch.object(driver, "dryrun") as dryrun:
        ConcreteAssets(config=config, dry_run=val)
        dryrun.assert_called_once_with(enable=val)


# Tests for workflow methods


def test_key_path(config):
    assetobj = ConcreteAssets(
        config={"foo": {"bar": config}},
        dry_run=False,
        batch=True,
        cycle=dt.datetime(2024, 3, 22, 18),
        key_path=["foo", "bar"],
        leadtime=dt.timedelta(hours=24),
    )
    assert config == assetobj._config


def test_Assets_validate(assetobj, caplog):
    log.setLevel(logging.INFO)
    assetobj.validate()
    assert regex_logged(caplog, "State: Ready")


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
def test_Assets__create_user_updated_config_base_file(
    assetobj, base_file, expected, tmp_path, update_values
):
    path = tmp_path / "updated.yaml"
    dc = assetobj._driver_config
    if not base_file:
        del dc["base_file"]
    if not update_values:
        del dc["update_values"]
    ConcreteAssets._create_user_updated_config(config_class=YAMLConfig, config_values=dc, path=path)
    with open(path, "r", encoding="utf-8") as f:
        updated = yaml.safe_load(f)
    assert updated == expected


def test_Assets__driver_config_fail(assetobj):
    del assetobj._config["concrete"]
    with raises(UWConfigError) as e:
        assert assetobj._driver_config
    assert str(e.value) == "Required 'concrete' block missing in config"


def test_Assets__driver_config_pass(assetobj):
    assert set(assetobj._driver_config.keys()) == {
        "base_file",
        "execution",
        "run_dir",
        "update_values",
    }


def test_Assets__rundir(assetobj):
    assert assetobj._rundir == Path(assetobj._driver_config["run_dir"])


def test_Assets__validate(assetobj):
    with patch.object(assetobj, "_validate", driver.Assets._validate):
        with patch.object(driver, "validate_internal") as validate_internal:
            assetobj._validate(assetobj)
        assert validate_internal.call_args_list[0].kwargs == {
            "schema_name": "concrete",
            "config": assetobj._config,
        }


# Driver Tests


def test_Driver(driverobj):
    assert Path(driverobj._driver_config["base_file"]).name == "base.yaml"
    assert driverobj._batch is True


# Tests for workflow methods


@pytest.mark.parametrize("batch", [True, False])
def test_Driver_run(batch, driverobj):
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


def test_Driver__run_via_batch_submission(driverobj):
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


def test_Driver__run_via_local_execution(driverobj):
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


def test_Driver__driver_config_fail(driverobj):
    del driverobj._config["concrete"]
    with raises(UWConfigError) as e:
        assert driverobj._driver_config
    assert str(e.value) == "Required 'concrete' block missing in config"


def test_Driver__driver_config_pass(driverobj):
    assert set(driverobj._driver_config.keys()) == {
        "base_file",
        "execution",
        "run_dir",
        "update_values",
    }


def test_Driver__namelist_schema_custom(driverobj, tmp_path):
    nmlschema = {"properties": {"n": {"type": "integer"}}, "type": "object"}
    schema = {"foo": {"bar": nmlschema}}
    schema_path = tmp_path / "test.jsonschema"
    with open(schema_path, "w", encoding="utf-8") as f:
        json.dump(schema, f)
    with patch.object(ConcreteDriver, "_driver_config", new_callable=PropertyMock) as dc:
        dc.return_value = {"baz": {"qux": {"validate": True}}}
        with patch.object(driver, "get_schema_file", return_value=schema_path):
            assert (
                driverobj._namelist_schema(config_keys=["baz", "qux"], schema_keys=["foo", "bar"])
                == nmlschema
            )


def test_Driver__namelist_schema_default(driverobj, tmp_path):
    nmlschema = {"properties": {"n": {"type": "integer"}}, "type": "object"}
    schema = {
        "properties": {
            "concrete": {"properties": {"namelist": {"properties": {"update_values": nmlschema}}}}
        }
    }
    schema_path = tmp_path / "test.jsonschema"
    with open(schema_path, "w", encoding="utf-8") as f:
        json.dump(schema, f)
    with patch.object(ConcreteDriver, "_driver_config", new_callable=PropertyMock) as dc:
        dc.return_value = {"namelist": {"validate": True}}
        with patch.object(driver, "get_schema_file", return_value=schema_path):
            assert driverobj._namelist_schema() == nmlschema


def test_Driver__namelist_schema_default_disable(driverobj):
    with patch.object(ConcreteDriver, "_driver_config", new_callable=PropertyMock) as dc:
        dc.return_value = {"namelist": {"validate": False}}
        assert driverobj._namelist_schema() == {"type": "object"}


def test_Driver__resources_fail(driverobj):
    del driverobj._config["platform"]
    with raises(UWConfigError) as e:
        assert driverobj._resources
    assert str(e.value) == "Required 'platform' block missing in config"


def test_Driver__resources_pass(driverobj):
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


def test_Driver__runcmd(driverobj):
    executable = driverobj._driver_config["execution"]["executable"]
    assert driverobj._runcmd == f"foo bar baz {executable}"


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


def test_Driver__runscript_done_file(driverobj):
    assert driverobj._runscript_done_file == "runscript.concrete.done"


def test_Driver__runscript_path(driverobj):
    assert driverobj._runscript_path == Path("/path/to/2024032218/run/runscript.concrete")


def test_Driver__scheduler(driverobj):
    with patch.object(driver, "JobScheduler") as JobScheduler:
        scheduler = JobScheduler.get_scheduler()
        assert driverobj._scheduler == scheduler
        JobScheduler.get_scheduler.assert_called_with(driverobj._resources)


def test_Driver__validate(assetobj):
    with patch.object(assetobj, "_validate", driver.Driver._validate):
        with patch.object(driver, "validate_internal") as validate_internal:
            assetobj._validate(assetobj)
        assert validate_internal.call_args_list[0].kwargs == {
            "schema_name": "concrete",
            "config": assetobj._config,
        }
        assert validate_internal.call_args_list[1].kwargs == {
            "schema_name": "platform",
            "config": assetobj._config,
        }


def test_Driver__write_runscript(driverobj, tmp_path):
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
