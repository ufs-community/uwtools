"""
ESGGrid driver tests.
"""

from pathlib import Path
from unittest.mock import patch

import f90nml  # type: ignore[import-untyped]
from pytest import fixture, mark, raises

from uwtools.drivers.driver import Driver
from uwtools.drivers.esg_grid import ESGGrid
from uwtools.exceptions import UWNotImplementedError

# Fixtures


@fixture
def config(tmp_path):
    return {
        "esg_grid": {
            "execution": {
                "batchargs": {
                    "export": "NONE",
                    "nodes": 1,
                    "stdout": "/path/to/file",
                    "walltime": "00:02:00",
                },
                "executable": "/path/to/esg_grid",
            },
            "namelist": {
                "update_values": {
                    "regional_grid_nml": {
                        "delx": 0.11,
                        "dely": 0.11,
                        "lx": -214,
                        "ly": -128,
                        "pazi": 0.0,
                        "plat": 38.5,
                        "plon": -97.5,
                    }
                }
            },
            "rundir": str(tmp_path),
        },
        "platform": {
            "account": "me",
            "scheduler": "slurm",
        },
    }


@fixture
def driverobj(config):
    return ESGGrid(config=config, batch=True)


# Tests


@mark.parametrize(
    "method",
    [
        "_run_resources",
        "_run_via_batch_submission",
        "_run_via_local_execution",
        "_runcmd",
        "_runscript",
        "_runscript_done_file",
        "_runscript_path",
        "_scheduler",
        "_validate",
        "_write_runscript",
        "output",
        "run",
        "runscript",
        "taskname",
    ],
)
def test_ESGGrid(method):
    assert getattr(ESGGrid, method) is getattr(Driver, method)


def test_ESGGrid_driver_name(driverobj):
    assert driverobj.driver_name() == ESGGrid.driver_name() == "esg_grid"


def test_ESGGrid_namelist_file(driverobj, logged):
    dst = driverobj.rundir / "regional_grid.nml"
    assert not dst.is_file()
    path = Path(driverobj.namelist_file().refs)
    assert dst.is_file()
    assert logged(f"Wrote config to {path}")
    assert isinstance(f90nml.read(dst), f90nml.Namelist)


def test_ESGGrid_namelist_file_fails_validation(driverobj, logged):
    driverobj._config["namelist"]["update_values"]["regional_grid_nml"]["delx"] = "string"
    path = Path(driverobj.namelist_file().refs)
    assert not path.exists()
    assert logged(f"Failed to validate {path}")
    assert logged("  'string' is not of type 'number'")


def test_ESGGrid_namelist_file_missing_base_file(driverobj, logged):
    base_file = str(Path(driverobj.config["rundir"], "missing.nml"))
    driverobj._config["namelist"]["base_file"] = base_file
    path = Path(driverobj.namelist_file().refs)
    assert not path.exists()
    assert logged("missing.nml: Not ready [external asset]")


def test_ESGGrid_output(driverobj):
    with raises(UWNotImplementedError) as e:
        assert driverobj.output
    assert str(e.value) == "The output() method is not yet implemented for this driver"


def test_ESGGrid_provisioned_rundir(driverobj, ready_task):
    with patch.multiple(
        driverobj,
        namelist_file=ready_task,
        runscript=ready_task,
    ) as mocks:
        driverobj.provisioned_rundir()
    for m in mocks:
        mocks[m].assert_called_once_with()
