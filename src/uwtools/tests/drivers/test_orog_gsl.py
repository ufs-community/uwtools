# pylint: disable=missing-function-docstring,protected-access,redefined-outer-name
"""
orog_gsl driver tests.
"""
from pathlib import Path
from unittest.mock import DEFAULT as D
from unittest.mock import patch

from pytest import fixture, mark

from uwtools.drivers.driver import Driver
from uwtools.drivers.orog_gsl import OrogGSL

# Fixtures


@fixture
def config(tmp_path):
    afile = tmp_path / "afile"
    afile.touch()
    return {
        "orog_gsl": {
            "config": {
                "halo": 4,
                "input_grid_file": str(afile),
                "resolution": 403,
                "tile": 7,
                "topo_data_2p5m": str(afile),
                "topo_data_30s": str(afile),
            },
            "execution": {
                "batchargs": {
                    "walltime": "00:01:00",
                },
                "executable": "/path/to/orog_gsl",
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
    return OrogGSL(config=config, batch=True)


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
        "_taskname",
        "_validate",
        "_write_runscript",
        "run",
        "runscript",
    ],
)
def test_OrogGSL(method):
    assert getattr(OrogGSL, method) is getattr(Driver, method)


def test_OrogGSL_input_grid_file(driverobj):
    path = Path(driverobj._config["rundir"]) / "C403_grid.tile7.halo4.nc"
    assert not path.is_file()
    driverobj.input_grid_file()
    assert path.is_symlink()


def test_OrogGSL_provisioned_rundir(driverobj):
    with patch.multiple(
        driverobj, input_grid_file=D, runscript=D, topo_data_2p5m=D, topo_data_30s=D
    ) as mocks:
        driverobj.provisioned_rundir()
    for m in mocks:
        mocks[m].assert_called_once_with()


def test_OrogGSL_topo_data_2p5m(driverobj):
    path = Path(driverobj._config["rundir"]) / "geo_em.d01.lat-lon.2.5m.HGT_M.nc"
    assert not path.is_file()
    driverobj.topo_data_2p5m()
    assert path.is_symlink()


def test_OrogGSL_topo_data_3os(driverobj):
    path = Path(driverobj._config["rundir"]) / "HGT.Beljaars_filtered.lat-lon.30s_res.nc"
    assert not path.is_file()
    driverobj.topo_data_30s()
    assert path.is_symlink()


def test_OrogGSL__driver_name(driverobj):
    assert driverobj._driver_name == "orog_gsl"


def test_OrogGSL__runcmd(driverobj):
    inputs = [str(driverobj._config["config"][k]) for k in ("tile", "resolution", "halo")]
    assert driverobj._runcmd == "echo '%s' | %s" % (
        "\n".join(inputs),
        driverobj._config["execution"]["executable"],
    )
