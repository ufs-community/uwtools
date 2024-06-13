# pylint: disable=missing-function-docstring,protected-access,redefined-outer-name
"""
orog_gsl driver tests.
"""
from pathlib import Path
from unittest.mock import DEFAULT as D
from unittest.mock import patch

from pytest import fixture

from uwtools.drivers import orog_gsl
from uwtools.scheduler import Slurm

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
            "run_dir": str(tmp_path),
        },
        "platform": {
            "account": "me",
            "scheduler": "slurm",
        },
    }


@fixture
def driverobj(config):
    return orog_gsl.OrogGSL(config=config, batch=True)


# Tests


def test_OrogGSL(driverobj):
    assert isinstance(driverobj, orog_gsl.OrogGSL)


def test_OrogGSL_input_grid_file(driverobj):
    path = Path(driverobj._driver_config["run_dir"]) / "C403_grid.tile7.halo4.nc"
    assert not path.is_file()
    driverobj.input_grid_file()
    assert path.is_symlink()


def test_OrogGSL_provisioned_run_directory(driverobj):
    with patch.multiple(
        driverobj, input_grid_file=D, runscript=D, topo_data_2p5m=D, topo_data_30s=D
    ) as mocks:
        driverobj.provisioned_run_directory()
    for m in mocks:
        mocks[m].assert_called_once_with()


def test_OrogGSL_run_batch(driverobj):
    with patch.object(driverobj, "_run_via_batch_submission") as func:
        driverobj.run()
    func.assert_called_once_with()


def test_OrogGSL_run_local(driverobj):
    driverobj._batch = False
    with patch.object(driverobj, "_run_via_local_execution") as func:
        driverobj.run()
    func.assert_called_once_with()


def test_OrogGSL_topo_data_2p5m(driverobj):
    path = Path(driverobj._driver_config["run_dir"]) / "geo_em.d01.lat-lon.2.5m.HGT_M.nc"
    assert not path.is_file()
    driverobj.topo_data_2p5m()
    assert path.is_symlink()


def test_OrogGSL_topo_data_3os(driverobj):
    path = Path(driverobj._driver_config["run_dir"]) / "HGT.Beljaars_filtered.lat-lon.30s_res.nc"
    assert not path.is_file()
    driverobj.topo_data_30s()
    assert path.is_symlink()


def test_OrogGSL__runcmd(driverobj):
    inputs = [str(driverobj._driver_config["config"][k]) for k in ("tile", "resolution", "halo")]
    assert driverobj._runcmd == "echo '%s' | %s" % (
        "\n".join(inputs),
        driverobj._driver_config["execution"]["executable"],
    )


def test_OrogGSL_runscript(driverobj):
    with patch.object(driverobj, "_runscript") as runscript:
        driverobj.runscript()
        runscript.assert_called_once()
        args = ("envcmds", "envvars", "execution", "scheduler")
        types = [list, dict, list, Slurm]
        assert [type(runscript.call_args.kwargs[x]) for x in args] == types


def test_OrogGSL__driver_config(driverobj):
    assert driverobj._driver_config == driverobj._config["orog_gsl"]


def test_OrogGSL__runscript_path(driverobj):
    assert driverobj._runscript_path == driverobj._rundir / "runscript.orog_gsl"


def test_OrogGSL__taskname(driverobj):
    assert driverobj._taskname("foo") == "orog_gsl foo"


def test_OrogGSL__validate(driverobj):
    driverobj._validate()
