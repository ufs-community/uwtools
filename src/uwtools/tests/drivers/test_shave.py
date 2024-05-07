# pylint: disable=missing-function-docstring,protected-access,redefined-outer-name
"""
Shave driver tests.
"""
from unittest.mock import DEFAULT as D
from unittest.mock import patch

import yaml
from pytest import fixture

from uwtools.drivers import shave
from uwtools.scheduler import Slurm

# Driver fixtures


@fixture
def config(tmp_path):
    return {
        "shave": {
            "execution": {
                "batchargs": {
                    "export": "NONE",
                    "nodes": 1,
                    "stdout": "/path/to/file",
                    "walltime": "00:02:00",
                },
                "executable": "/path/to/shave",
            },
            "config": {
                "input_grid_file": "/path/to/input/grid/file.nc",
                "nh4": 1,
                "nx": 214,
                "ny": 128,
            },
            "run_dir": str(tmp_path),
        },
        "platform": {
            "account": "me",
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
    return shave.Shave(config=config_file, batch=True)


# Driver tests


def test_Shave(driverobj):
    assert isinstance(driverobj, shave.Shave)


def test_Shave_dry_run(config_file):
    with patch.object(shave, "dryrun") as dryrun:
        driverobj = shave.Shave(config=config_file, batch=True, dry_run=True)
    assert driverobj._dry_run is True
    dryrun.assert_called_once_with()


def test_Shave_provisioned_run_directory(driverobj):
    with patch.multiple(
        driverobj,
        runscript=D,
    ) as mocks:
        driverobj.provisioned_run_directory()
    for m in mocks:
        mocks[m].assert_called_once_with()


def test_Shave_run_batch(driverobj):
    with patch.object(driverobj, "_run_via_batch_submission") as func:
        driverobj.run()
    func.assert_called_once_with()


def test_Shave_run_local(driverobj):
    driverobj._batch = False
    with patch.object(driverobj, "_run_via_local_execution") as func:
        driverobj.run()
    func.assert_called_once_with()


def test_Shave__runcmd(driverobj):
    cmd = driverobj._runcmd
    nx = driverobj._driver_config["config"]["nx"]
    ny = driverobj._driver_config["config"]["ny"]
    nh4 = driverobj._driver_config["config"]["nh4"]
    input_file_path = driverobj._driver_config["config"]["input_grid_file"]
    output_file_path = input_file_path.replace(".nc", "_NH0.nc")
    assert cmd == f"/path/to/shave {nx} {ny} {nh4} {input_file_path} {output_file_path}"


def test_Shave_runscript(driverobj):
    with patch.object(driverobj, "_runscript") as runscript:
        driverobj.runscript()
        runscript.assert_called_once()
        args = ("envcmds", "envvars", "execution", "scheduler")
        types = [list, dict, list, Slurm]
        assert [type(runscript.call_args.kwargs[x]) for x in args] == types


def test_Shave__driver_config(driverobj):
    assert driverobj._driver_config == driverobj._config["shave"]


def test_Shave__runscript_path(driverobj):
    assert driverobj._runscript_path == driverobj._rundir / "runscript.shave"


def test_Shave__taskname(driverobj):
    assert driverobj._taskname("foo") == "shave foo"


def test_Shave__validate(driverobj):
    driverobj._validate()
