# pylint: disable=missing-function-docstring,protected-access,redefined-outer-name
"""
WaveWatchIII driver tests.
"""
import datetime as dt
from unittest.mock import DEFAULT as D
from unittest.mock import patch

import yaml
from pytest import fixture, mark

from uwtools.drivers.driver import AssetsCycleBased
from uwtools.drivers.ww3 import WaveWatchIII

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
            "rundir": str(tmp_path / "run"),
        },
    }


@fixture
def cycle():
    return dt.datetime(2024, 2, 1, 18)


@fixture
def driverobj(config, cycle):
    return WaveWatchIII(config=config, cycle=cycle)


# Tests


@mark.parametrize(
    "method",
    [
        "_driver_config",
        "_taskname",
        "_validate",
    ],
)
def test_WaveWatchIII(method):
    assert getattr(WaveWatchIII, method) is getattr(AssetsCycleBased, method)


def test_WaveWatchIII_namelist_file(driverobj):
    src = driverobj._driver_config["namelist"]["template_file"]
    with open(src, "w", encoding="utf-8") as f:
        yaml.dump({}, f)
    dst = driverobj._rundir / "ww3_shel.nml"
    assert not dst.is_file()
    driverobj.namelist_file()
    assert dst.is_file()


def test_WaveWatchIII_provisioned_rundir(driverobj):
    with patch.multiple(
        driverobj,
        namelist_file=D,
        restart_directory=D,
    ) as mocks:
        driverobj.provisioned_rundir()
    for m in mocks:
        mocks[m].assert_called_once_with()


def test_WaveWatchIII_restart_directory(driverobj):
    path = driverobj._rundir / "restart_wave"
    assert not path.is_dir()
    driverobj.restart_directory()
    assert path.is_dir()


def test_WaveWatchIII__driver_name(driverobj):
    assert driverobj._driver_name == "ww3"
