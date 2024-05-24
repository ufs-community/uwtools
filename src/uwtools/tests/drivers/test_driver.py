# pylint: disable=missing-function-docstring,protected-access,redefined-outer-name
"""
Tests for uwtools.drivers.driver module.
"""
import datetime as dt
import json
import logging
from pathlib import Path
from unittest.mock import patch

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
def driverobj(config):
    return ConcreteDriver(
        config=config,
        dry_run=False,
        batch=True,
        cycle=dt.datetime(2024, 3, 22, 18),
        leadtime=dt.timedelta(hours=24),
    )


# Tests


def test_Driver(driverobj):
    assert Path(driverobj._driver_config["base_file"]).name == "base.yaml"
    assert driverobj._batch is True


def test_Driver_cycle_leadtime_error(config):
    with raises(UWError) as e:
        ConcreteDriver(config=config, leadtime=dt.timedelta(hours=24))
    assert "When leadtime is specified, cycle is required" in str(e)


@pytest.mark.parametrize("val", (True, False))
def test_Driver_dry_run(config, val):
    with patch.object(driver, "dryrun") as dryrun:
        ConcreteDriver(config=config, dry_run=val)
        dryrun.assert_called_once_with(enable=val)


# Tests for workflow methods


def test_key_path(config):
    driverobj = ConcreteDriver(
        config={"foo": {"bar": config}},
        dry_run=False,
        batch=True,
        cycle=dt.datetime(2024, 3, 22, 18),
        key_path=["foo", "bar"],
        leadtime=dt.timedelta(hours=24),
    )
    assert config == driverobj._config


def test_Driver_validate(caplog, driverobj):
    log.setLevel(logging.INFO)
    driverobj.validate()
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


def test_Driver__resources_fail(driverobj):
    del driverobj._config["platform"]
    with raises(UWConfigError) as e:
        assert driverobj._resources
    assert str(e.value) == "Required 'platform' block missing in config"


def test_Driver__resources_pass(driverobj):
    account = "me"
    walltime = "00:05:00"
    driverobj._driver_config["execution"].update({"batchargs": {"walltime": walltime}})
    assert driverobj._resources == {
        "account": account,
        "rundir": driverobj._rundir,
    }


def test_Driver__rundir(driverobj):
    assert driverobj._rundir == Path("/path/to/2024032218/run")


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
