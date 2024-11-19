# pylint: disable=missing-function-docstring,protected-access,redefined-outer-name
"""
Shave driver tests.
"""
from pathlib import Path
from unittest.mock import DEFAULT as D
from unittest.mock import patch

from pytest import fixture, mark, raises

from uwtools.drivers.driver import Driver
from uwtools.drivers.shave import Shave
from uwtools.exceptions import UWNotImplementedError

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
                "input_grid_file": str(tmp_path / "input_file.nc"),
                "output_grid_file": "/path/to/input/grid/file.nc",
                "nhalo": 1,
                "nx": 214,
                "ny": 128,
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
    return Shave(config=config, batch=True)


# Tests


@mark.parametrize(
    "method",
    [
        "_run_resources",
        "_run_via_batch_submission",
        "_run_via_local_execution",
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
def test_Shave(method):
    assert getattr(Shave, method) is getattr(Driver, method)


def test_Shave_driver_name(driverobj):
    assert driverobj.driver_name() == Shave.driver_name() == "shave"


def test_Shave_input_config_file(driverobj):
    nx = driverobj.config["config"]["nx"]
    ny = driverobj.config["config"]["ny"]
    nhalo = driverobj.config["config"]["nhalo"]
    input_file_path = driverobj._config["config"]["input_grid_file"]
    Path(input_file_path).touch()
    output_file_path = driverobj._config["config"]["output_grid_file"]
    driverobj.input_config_file()
    with open(driverobj._input_config_path, "r", encoding="utf-8") as cfg_file:
        content = cfg_file.readlines()
    content = [l.strip("\n") for l in content]
    assert len(content) == 1
    assert content[0] == f"{nx} {ny} {nhalo} '{input_file_path}' '{output_file_path}'"


def test_Shave_output(driverobj):
    with raises(UWNotImplementedError) as e:
        assert driverobj.output
    assert str(e.value) == "The output() method is not yet implemented for this driver"


def test_Shave_provisioned_rundir(driverobj):
    with patch.multiple(
        driverobj,
        input_config_file=D,
        runscript=D,
    ) as mocks:
        driverobj.provisioned_rundir()
    for m in mocks:
        mocks[m].assert_called_once_with()


def test_Shave__runcmd(driverobj):
    cmd = driverobj._runcmd
    assert cmd == "/path/to/shave < shave.cfg"
