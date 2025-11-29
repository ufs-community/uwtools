"""
make_solo_mosaic driver tests.
"""

from unittest.mock import Mock, patch

import iotaa
from pytest import fixture

from uwtools.drivers.make_solo_mosaic import MakeSoloMosaic

# Fixtures


@fixture
def config(tmp_path):
    return {
        "make_solo_mosaic": {
            "config": {
                "dir": str(tmp_path / "input" / "input_grid_file"),
                "num_tiles": 1,
            },
            "execution": {
                "batchargs": {
                    "cores": 1,
                    "walltime": "00:01:00",
                },
                "executable": "/path/to/make_solo_mosaic.exe",
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
    return MakeSoloMosaic(config=config, batch=True)


# Tests


def test_MakeSoloMosaic_driver_name(driverobj):
    assert driverobj.driver_name() == MakeSoloMosaic.driver_name() == "make_solo_mosaic"


def test_MakeSoloMosaic_output(driverobj):
    assert driverobj.output["path"] == driverobj.rundir / "mosaic.nc"
    driverobj._config["config"]["mosaic_name"] = "foo"
    assert driverobj.output["path"] == driverobj.rundir / "foo.nc"


def test_MakeSoloMosaic_provisioned_rundir(driverobj):
    node = Mock(spec=iotaa.Node)
    with patch.object(driverobj, "runscript", return_value=node) as runscript:
        driverobj.provisioned_rundir()
        runscript.assert_called_once_with()


def test_MakeSoloMosaic_taskname(driverobj):
    assert driverobj.taskname("foo") == "make_solo_mosaic foo"


def test_MakeSoloMosaic__runcmd(driverobj):
    dir_path = driverobj.config["config"]["dir"]
    cmd = driverobj._runcmd
    assert cmd == f"/path/to/make_solo_mosaic.exe --dir {dir_path} --num_tiles 1"


def test_MakeSoloMosaic__validate(driverobj):
    driverobj._validate()
