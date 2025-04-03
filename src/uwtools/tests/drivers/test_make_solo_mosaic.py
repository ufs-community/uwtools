"""
make_solo_mosaic driver tests.
"""

from unittest.mock import patch

from pytest import fixture, mark, raises

from uwtools.drivers.driver import Driver
from uwtools.drivers.make_solo_mosaic import MakeSoloMosaic
from uwtools.exceptions import UWNotImplementedError

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
    ],
)
def test_MakeSoloMosaic(method):
    assert getattr(MakeSoloMosaic, method) is getattr(Driver, method)


def test_MakeSoloMosaic_driver_name(driverobj):
    assert driverobj.driver_name() == MakeSoloMosaic.driver_name() == "make_solo_mosaic"


def test_MakeSoloMosaic_output(driverobj):
    with raises(UWNotImplementedError) as e:
        assert driverobj.output
    assert str(e.value) == "The output() method is not yet implemented for this driver"


def test_MakeSoloMosaic_provisioned_rundir(driverobj):
    with patch.object(driverobj, "runscript") as runscript:
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
