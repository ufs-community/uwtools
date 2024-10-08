# pylint: disable=missing-function-docstring,protected-access,redefined-outer-name
"""
make_hgrid driver tests.
"""
from unittest.mock import DEFAULT as D
from unittest.mock import patch

from pytest import fixture, mark

from uwtools.drivers.driver import Driver
from uwtools.drivers.make_hgrid import MakeHgrid

# Fixtures


@fixture
def config(tmp_path):
    return {
        "make_hgrid": {
            "config": {
                "grid_type": "gnomonic_ed",
                "halo": 1,
                "nest_grids": 1,
                "parent_tile": [6],
                "verbose": True,
            },
            "execution": {
                "batchargs": {
                    "cores": 1,
                    "walltime": "00:01:00",
                },
                "executable": "/path/to/make_hgrid",
            },
            "rundir": str(tmp_path),
        },
        "platform": {
            "account": "myaccount",
            "scheduler": "slurm",
        },
    }


@fixture
def driverobj(config):
    return MakeHgrid(config=config, batch=True)


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
        "run",
        "runscript",
        "taskname",
    ],
)
def test_MakeHgrid(method):
    assert getattr(MakeHgrid, method) is getattr(Driver, method)


def test_MakeHgrid_driver_name(driverobj):
    assert driverobj.driver_name() == MakeHgrid.driver_name() == "make_hgrid"


def test_MakeHgrid_provisioned_rundir(driverobj):
    with patch.multiple(driverobj, runscript=D) as mocks:
        driverobj.provisioned_rundir()
    for m in mocks:
        mocks[m].assert_called_once_with()


def test_MakeHgrid__runcmd(driverobj):
    expected = [
        "/path/to/make_hgrid",
        "--grid_type gnomonic_ed",
        "--halo 1",
        "--nest_grids 1",
        "--parent_tile 6",
        "--verbose",
    ]
    assert driverobj._runcmd == " ".join(expected)
