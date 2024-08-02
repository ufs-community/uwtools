# pylint: disable=missing-function-docstring,protected-access,redefined-outer-name
"""
SCHISM driver tests.
"""
import datetime as dt
from unittest.mock import DEFAULT as D
from unittest.mock import patch

import yaml
from pytest import fixture, mark

from uwtools.drivers.driver import AssetsCycleBased
from uwtools.drivers.schism import SCHISM

# Fixtures


@fixture
def config(tmp_path):
    return {
        "schism": {
            "namelist": {
                "template_file": str(tmp_path / "param.nml.IN"),
                "template_values": {
                    "dt": 100,
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
    return SCHISM(config=config, cycle=cycle)


# Tests


@mark.parametrize(
    "method",
    ["_taskname", "_validate"],
)
def test_SCHISM(method):
    assert getattr(SCHISM, method) is getattr(AssetsCycleBased, method)


def test_SCHISM_namelist_file(driverobj):
    src = driverobj._config["namelist"]["template_file"]
    with open(src, "w", encoding="utf-8") as f:
        yaml.dump({}, f)
    dst = driverobj._rundir / "param.nml"
    assert not dst.is_file()
    driverobj.namelist_file()
    assert dst.is_file()


def test_SCHISM_provisioned_rundir(driverobj):
    with patch.multiple(
        driverobj,
        namelist_file=D,
    ) as mocks:
        driverobj.provisioned_rundir()
    for m in mocks:
        mocks[m].assert_called_once_with()


def test_SCHISM__driver_name(driverobj):
    assert driverobj._driver_name == "schism"
