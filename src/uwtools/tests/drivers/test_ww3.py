# pylint: disable=missing-function-docstring,protected-access,redefined-outer-name
"""
WaveWatchIII driver tests.
"""
import datetime as dt
from unittest.mock import DEFAULT as D
from unittest.mock import patch

import yaml
from pytest import fixture

from uwtools.drivers import ww3

# Fixtures


@fixture
def config(tmp_path):
    return {
        "ww3": {
            "namelist": {
                "template_file": str(tmp_path / "ww3_shel.nml.IN"),
                "template_values": {
                    "input_forcing_winds": "C",
                },
            },
            "run_dir": str(tmp_path),
        },
    }


@fixture
def config_file(config, tmp_path):
    path = tmp_path / "config.yaml"
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(config, f)
    return path


@fixture
def cycle():
    return dt.datetime(2024, 2, 1, 18)


@fixture
def driverobj(config_file, cycle):
    return ww3.WaveWatchIII(config=config_file, cycle=cycle, batch=True)


# Tests


def test_WaveWatchIII(driverobj):
    assert isinstance(driverobj, ww3.WaveWatchIII)


def test_WaveWatchIII_namelist_file(driverobj):
    src = driverobj._driver_config["namelist"]["template_file"]
    with open(src, "w", encoding="utf-8") as f:
        yaml.dump({}, f)
    dst = driverobj._rundir / "ww3_shel.nml"
    assert not dst.is_file()
    driverobj.namelist_file()
    assert dst.is_file()


def test_WaveWatchIII_provisioned_run_directory(driverobj):
    with patch.multiple(
        driverobj,
        namelist_file=D,
        restart_directory=D,
    ) as mocks:
        driverobj.provisioned_run_directory()
    for m in mocks:
        mocks[m].assert_called_once_with()


def test_WaveWatchIII_restart_directory(driverobj):
    path = driverobj._rundir / "restart_wave"
    assert not path.is_dir()
    driverobj.restart_directory()
    assert path.is_dir()


def test_WaveWatchIII__driver_config(driverobj):
    assert driverobj._driver_config == driverobj._config["ww3"]


def test_WaveWatchIII__validate(driverobj):
    driverobj._validate()
