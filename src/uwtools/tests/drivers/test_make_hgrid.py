"""
make_hgrid driver tests.
"""

from unittest.mock import patch

from pytest import fixture

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


def test_MakeHgrid_driver_name(driverobj):
    assert driverobj.driver_name() == MakeHgrid.driver_name() == "make_hgrid"


def test_MakeHgrid_output(driverobj):
    assert driverobj.output["path"] == driverobj.rundir / "horizontal_grid.nc"
    driverobj._config["config"]["grid_name"] = "foo"
    assert driverobj.output["path"] == driverobj.rundir / "foo.nc"


def test_MakeHgrid_provisioned_rundir(driverobj, ready_task):
    with patch.multiple(driverobj, runscript=ready_task):
        assert driverobj.provisioned_rundir().ready


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
