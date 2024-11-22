# pylint: disable=missing-function-docstring,protected-access,redefined-outer-name
"""
global_equiv_resol driver tests.
"""
from pathlib import Path
from unittest.mock import patch

from pytest import fixture, mark, raises

from uwtools.drivers.driver import Driver
from uwtools.drivers.global_equiv_resol import GlobalEquivResol
from uwtools.exceptions import UWNotImplementedError

# Fixtures


@fixture
def config(tmp_path):
    return {
        "global_equiv_resol": {
            "execution": {
                "batchargs": {
                    "cores": 1,
                    "walltime": "00:01:00",
                },
                "executable": "/path/to/global_equiv_resol.exe",
            },
            "rundir": str(tmp_path),
            "input_grid_file": str(tmp_path / "input" / "input_grid_file"),
        },
        "platform": {
            "account": "myaccount",
            "scheduler": "slurm",
        },
    }


@fixture
def driverobj(config):
    return GlobalEquivResol(config=config, batch=True)


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
def test_GlobalEquivResol(method):
    assert getattr(GlobalEquivResol, method) is getattr(Driver, method)


def test_GlobalEquivResol_driver_name(driverobj):
    assert driverobj.driver_name() == GlobalEquivResol.driver_name() == "global_equiv_resol"


def test_GlobalEquivResol_input_file(driverobj):
    path = Path(driverobj.config["input_grid_file"])
    assert not driverobj.input_file().ready()
    path.parent.mkdir()
    path.touch()
    assert driverobj.input_file().ready()


def test_GlobalEquivResol_output(driverobj):
    with raises(UWNotImplementedError) as e:
        assert driverobj.output
    assert str(e.value) == "The output() method is not yet implemented for this driver"


def test_GlobalEquivResol_provisioned_rundir(driverobj, oktask):
    with patch.multiple(
        driverobj,
        input_file=oktask,
        runscript=oktask,
    ) as mocks:
        driverobj.provisioned_rundir()
    for m in mocks:
        mocks[m].assert_called_once_with()


def test_GlobalEquivResol__runcmd(driverobj):
    cmd = driverobj._runcmd
    input_file_path = driverobj.config["input_grid_file"]
    assert cmd == f"/path/to/global_equiv_resol.exe {input_file_path}"
