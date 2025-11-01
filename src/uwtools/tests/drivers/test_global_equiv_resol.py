"""
global_equiv_resol driver tests.
"""

from pathlib import Path
from unittest.mock import patch

from pytest import fixture

from uwtools.drivers.global_equiv_resol import GlobalEquivResol

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


def test_GlobalEquivResol_driver_name(driverobj):
    assert driverobj.driver_name() == GlobalEquivResol.driver_name() == "global_equiv_resol"


def test_GlobalEquivResol_input_file(driverobj):
    path = Path(driverobj.config["input_grid_file"])
    assert not driverobj.input_file().ref.is_file()
    path.parent.mkdir()
    path.touch()
    assert driverobj.input_file().ref.is_file()


def test_GlobalEquivResol_output(driverobj):
    assert driverobj.output["path"] == Path(driverobj.config["input_grid_file"])


def test_GlobalEquivResol_provisioned_rundir(driverobj, ready_task):
    with patch.multiple(
        driverobj,
        input_file=ready_task,
        runscript=ready_task,
    ):
        assert driverobj.provisioned_rundir().ready


def test_GlobalEquivResol__runcmd(driverobj):
    cmd = driverobj._runcmd
    input_file_path = driverobj.config["input_grid_file"]
    assert cmd == f"/path/to/global_equiv_resol.exe {input_file_path}"
