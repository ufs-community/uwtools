"""
SCHISM driver tests.
"""

from pathlib import Path
from unittest.mock import patch

import yaml
from pytest import fixture

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
def cycle(utc):
    return utc(2024, 2, 1, 18)


@fixture
def driverobj(config, cycle):
    return SCHISM(config=config, cycle=cycle)


# Tests


def test_SCHISM_driver_name(driverobj):
    assert driverobj.driver_name() == SCHISM.driver_name() == "schism"


def test_SCHISM_namelist_file(driverobj):
    src = driverobj.config["namelist"]["template_file"]
    Path(src).write_text(yaml.dump({}))
    dst = driverobj.rundir / "param.nml"
    assert not dst.is_file()
    driverobj.namelist_file()
    assert dst.is_file()


def test_SCHISM_provisioned_rundir(driverobj, ready_task):
    with patch.multiple(
        driverobj,
        namelist_file=ready_task,
    ):
        assert driverobj.provisioned_rundir().ready
