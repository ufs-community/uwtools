# pylint: disable=missing-function-docstring,protected-access,redefined-outer-name
"""
make_solo_mosaic driver tests.
"""
from unittest.mock import DEFAULT as D
from unittest.mock import patch

import yaml
from pytest import fixture

from uwtools.drivers import make_solo_mosaic
from uwtools.scheduler import Slurm

# Driver fixtures


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
            "run_dir": str(tmp_path),
        },
        "platform": {
            "account": "myaccount",
            "scheduler": "slurm",
        },
    }


@fixture
def config_file(config, tmp_path):
    path = tmp_path / "config.yaml"
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(config, f)
    return path


@fixture
def driverobj(config_file):
    return make_solo_mosaic.MakeSoloMosaic(config=config_file, batch=True)


# Driver tests


def test_MakeSoloMosaic(driverobj):
    assert isinstance(driverobj, make_solo_mosaic.MakeSoloMosaic)


def test_MakeSoloMosaic_dry_run(config_file):
    with patch.object(make_solo_mosaic, "dryrun") as dryrun:
        driverobj = make_solo_mosaic.MakeSoloMosaic(config=config_file, batch=True, dry_run=True)
    assert driverobj._dry_run is True
    dryrun.assert_called_once_with()


def test_MakeSoloMosaic_provisioned_run_directory(driverobj):
    with patch.multiple(
        driverobj,
        runscript=D,
    ) as mocks:
        driverobj.provisioned_run_directory()
    for m in mocks:
        mocks[m].assert_called_once_with()


def test_MakeSoloMosaic_run_batch(driverobj):
    with patch.object(driverobj, "_run_via_batch_submission") as func:
        driverobj.run()
    func.assert_called_once_with()


def test_MakeSoloMosaic_run_local(driverobj):
    driverobj._batch = False
    with patch.object(driverobj, "_run_via_local_execution") as func:
        driverobj.run()
    func.assert_called_once_with()


def test_MakeSoloMosaic_runscript(driverobj):
    with patch.object(driverobj, "_runscript") as runscript:
        driverobj.runscript()
        runscript.assert_called_once()
        args = ("envcmds", "envvars", "execution", "scheduler")
        types = [list, dict, list, Slurm]
        assert [type(runscript.call_args.kwargs[x]) for x in args] == types


def test_MakeSoloMosaic__driver_config(driverobj):
    assert driverobj._driver_config == driverobj._config["make_solo_mosaic"]


def test_MakeSoloMosaic__runscript_path(driverobj):
    assert driverobj._runscript_path == driverobj._rundir / "runscript.make_solo_mosaic"


def test_MakeSoloMosaic__taskname(driverobj):
    assert driverobj._taskname("foo") == "make_solo_mosaic foo"


def test_MakeSoloMosaic__validate(driverobj):
    driverobj._validate()
