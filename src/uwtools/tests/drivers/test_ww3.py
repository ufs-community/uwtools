# pylint: disable=missing-function-docstring,protected-access,redefined-outer-name
"""
WW3 driver tests.
"""
import logging
from pathlib import Path
from unittest.mock import DEFAULT as D
from unittest.mock import patch

import f90nml  # type: ignore
import yaml
from iotaa import refs
from pytest import fixture

from uwtools.drivers import ww3
from uwtools.logging import log
from uwtools.tests.support import logged

# Fixtures


@fixture
def config(tmp_path):
    return {
        "ww3": {
            "namelist": {
                "update_values": {
                    "input_nml": {
                        "input_forcing_winds": "C",
                    },
                },
            },
            "run_dir": str(tmp_path),
        },
        "platform": {
            "account": "me",
            "scheduler": "slurm",
        },
    }


@fixture
def config_file(config, tmp_path):
    path = tmp_path / "config.yaml"
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(config, f)
    return path


@fixture
def driverobj(config_file):
    return ww3.WaveWatchIII(config=config_file, batch=True)


# Tests


def test_WaveWatchIII(driverobj):
    assert isinstance(driverobj, ww3.WaveWatchIII)


def test_WaveWatchIII_namelist_file(caplog, driverobj):
    log.setLevel(logging.DEBUG)
    dst = driverobj._rundir / "ww3_shel.nml"
    assert not dst.is_file()
    path = Path(refs(driverobj.namelist_file()))
    assert dst.is_file()
    assert logged(caplog, f"Wrote config to {path}")
    assert isinstance(f90nml.read(dst), f90nml.Namelist)


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
