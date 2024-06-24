# pylint: disable=missing-function-docstring,protected-access,redefined-outer-name
"""
Shave driver tests.
"""
from unittest.mock import DEFAULT as D
from unittest.mock import patch

from pytest import fixture, mark

from uwtools.drivers.driver import Driver
from uwtools.drivers.shave import Shave

# Fixtures


@fixture
def config(tmp_path):
    return {
        "shave": {
            "execution": {
                "batchargs": {
                    "export": "NONE",
                    "nodes": 1,
                    "stdout": "/path/to/file",
                    "walltime": "00:02:00",
                },
                "executable": "/path/to/shave",
            },
            "config": {
                "input_grid_file": "/path/to/input/grid/file.nc",
                "nh4": 1,
                "nx": 214,
                "ny": 128,
            },
            "run_dir": str(tmp_path),
        },
        "platform": {
            "account": "me",
            "scheduler": "slurm",
        },
    }


@fixture
def driverobj(config):
    return Shave(config=config, batch=True)


# Tests


@mark.parametrize(
    "method",
    [
        "_driver_config",
        "_resources",
        "_run_via_batch_submission",
        "_run_via_local_execution",
        "_runscript",
        "_runscript_done_file",
        "_runscript_path",
        "_scheduler",
        "_taskname",
        "_validate",
        "_write_runscript",
        "run",
        "runscript",
    ],
)
def test_Shave(method):
    assert getattr(Shave, method) is getattr(Driver, method)


def test_Shave_provisioned_run_directory(driverobj):
    with patch.multiple(
        driverobj,
        runscript=D,
    ) as mocks:
        driverobj.provisioned_run_directory()
    for m in mocks:
        mocks[m].assert_called_once_with()


def test_Shave__driver_name(driverobj):
    assert driverobj._driver_name == "shave"


def test_Shave__runcmd(driverobj):
    cmd = driverobj._runcmd
    nx = driverobj._driver_config["config"]["nx"]
    ny = driverobj._driver_config["config"]["ny"]
    nh4 = driverobj._driver_config["config"]["nh4"]
    input_file_path = driverobj._driver_config["config"]["input_grid_file"]
    output_file_path = input_file_path.replace(".nc", "_NH0.nc")
    assert cmd == f"/path/to/shave {nx} {ny} {nh4} {input_file_path} {output_file_path}"
