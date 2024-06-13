# pylint: disable=missing-function-docstring,protected-access,redefined-outer-name
"""
SCHISM driver tests.
"""
import datetime as dt
from unittest.mock import DEFAULT as D
from unittest.mock import patch

import yaml
from pytest import fixture

from uwtools.drivers import schism

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
            "run_dir": str(tmp_path),
        },
    }


@fixture
def cycle():
    return dt.datetime(2024, 2, 1, 18)


@fixture
def driverobj(config, cycle):
    return schism.SCHISM(config=config, cycle=cycle, batch=True)


# Tests


def test_SCHISM(driverobj):
    assert isinstance(driverobj, schism.SCHISM)


def test_SCHISM_namelist_file(driverobj):
    src = driverobj._driver_config["namelist"]["template_file"]
    with open(src, "w", encoding="utf-8") as f:
        yaml.dump({}, f)
    dst = driverobj._rundir / "param.nml"
    assert not dst.is_file()
    driverobj.namelist_file()
    assert dst.is_file()


def test_SCHISM_provisioned_run_directory(driverobj):
    with patch.multiple(
        driverobj,
        namelist_file=D,
    ) as mocks:
        driverobj.provisioned_run_directory()
    for m in mocks:
        mocks[m].assert_called_once_with()


def test_SCHISM__driver_config(driverobj):
    assert driverobj._driver_config == driverobj._config["schism"]


def test_SCHISM__validate(driverobj):
    driverobj._validate()
