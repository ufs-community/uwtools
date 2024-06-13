# pylint: disable=missing-function-docstring,protected-access,redefined-outer-name
"""
make_hgrid driver tests.
"""
from unittest.mock import DEFAULT as D
from unittest.mock import patch

from pytest import fixture

from uwtools.drivers import make_hgrid
from uwtools.scheduler import Slurm

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
            "run_dir": str(tmp_path),
        },
        "platform": {
            "account": "myaccount",
            "scheduler": "slurm",
        },
    }


@fixture
def driverobj(config):
    return make_hgrid.MakeHgrid(config=config, batch=True)


# Tests


def test_MakeHgrid(driverobj):
    assert isinstance(driverobj, make_hgrid.MakeHgrid)


def test_MakeHgrid_provisioned_run_directory(driverobj):
    with patch.multiple(
        driverobj,
        runscript=D,
    ) as mocks:
        driverobj.provisioned_run_directory()
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


def test_MakeHgrid_run_batch(driverobj):
    with patch.object(driverobj, "_run_via_batch_submission") as func:
        driverobj.run()
    func.assert_called_once_with()


def test_MakeHgrid_run_local(driverobj):
    driverobj._batch = False
    with patch.object(driverobj, "_run_via_local_execution") as func:
        driverobj.run()
    func.assert_called_once_with()


def test_MakeHgrid_runscript(driverobj):
    with patch.object(driverobj, "_runscript") as runscript:
        driverobj.runscript()
        runscript.assert_called_once()
        args = ("envcmds", "envvars", "execution", "scheduler")
        types = [list, dict, list, Slurm]
        assert [type(runscript.call_args.kwargs[x]) for x in args] == types


def test_MakeHgrid__driver_config(driverobj):
    assert driverobj._driver_config == driverobj._config["make_hgrid"]


def test_MakeHgrid__runscript_path(driverobj):
    assert driverobj._runscript_path == driverobj._rundir / "runscript.make_hgrid"


def test_MakeHgrid__taskname(driverobj):
    assert driverobj._taskname("foo") == "make_hgrid foo"


def test_MakeHgrid__validate(driverobj):
    driverobj._validate()
