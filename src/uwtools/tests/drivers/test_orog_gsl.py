# pylint: disable=missing-function-docstring,protected-access,redefined-outer-name
"""
orog_gsl driver tests.
"""
from pathlib import Path
from unittest.mock import DEFAULT as D
from unittest.mock import patch

from pytest import fixture, mark, raises

from uwtools.drivers.driver import Driver
from uwtools.drivers.orog_gsl import OrogGSL
from uwtools.exceptions import UWNotImplementedError

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
        "_validate",
        "_write_runscript",
        "output",
        "run",
        "runscript",
        "taskname",
    ],
)
def test_OrogGSL(method):
    assert getattr(OrogGSL, method) is getattr(Driver, method)


def test_OrogGSL_driver_name(driverobj):
    assert driverobj.driver_name() == OrogGSL.driver_name() == "orog_gsl"


def test_OrogGSL_input_config_file(driverobj):
    driverobj.input_config_file()
    inputs = [str(driverobj.config["config"][k]) for k in ("tile", "resolution", "halo")]
    with open(driverobj._input_config_path, "r", encoding="utf-8") as cfg_file:
        content = cfg_file.readlines()
    content = [l.strip("\n") for l in content]
    assert len(content) == 3
    assert content == inputs


def test_OrogGSL_input_grid_file(driverobj):
    path = Path(driverobj.config["rundir"], "C403_grid.tile7.halo4.nc")
    assert not path.is_file()
    driverobj.input_grid_file()
    assert path.is_symlink()


def test_OrogGSL_output(driverobj):
    with raises(UWNotImplementedError) as e:
        assert driverobj.output
    assert str(e.value) == "The output() method is not yet implemented for this driver"


def test_OrogGSL_provisioned_rundir(driverobj):
    with patch.multiple(
        driverobj,
        input_config_file=D,
        input_grid_file=D,
        runscript=D,
        topo_data_2p5m=D,
        topo_data_30s=D,
    ) as mocks:
        driverobj.provisioned_rundir()
    for m in mocks:
        mocks[m].assert_called_once_with()


def test_OrogGSL_topo_data_2p5m(driverobj):
    path = Path(driverobj.config["rundir"], "geo_em.d01.lat-lon.2.5m.HGT_M.nc")
    assert not path.is_file()
    driverobj.topo_data_2p5m()
    assert path.is_symlink()


def test_OrogGSL_topo_data_3os(driverobj):
    path = Path(driverobj.config["rundir"], "HGT.Beljaars_filtered.lat-lon.30s_res.nc")
    assert not path.is_file()
    driverobj.topo_data_30s()
    assert path.is_symlink()


def test_OrogGSL__runcmd(driverobj):
    assert driverobj._runcmd == "%s < %s" % (
        driverobj.config["execution"]["executable"],
        driverobj._input_config_path.name,
    )
