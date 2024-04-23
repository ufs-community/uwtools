# pylint: disable=missing-function-docstring,protected-access,redefined-outer-name
"""
global_equiv_resol driver tests.
"""
from pathlib import Path
from unittest.mock import DEFAULT as D
from unittest.mock import patch

import yaml
from pytest import fixture

from uwtools.drivers import make_hgrid
from uwtools.scheduler import Slurm

# Driver fixtures


@fixture
def config(tmp_path):
    return {
        "make_hgrid": {
            "execution": {
                "batchargs": {
                    "cores": 1,
                    "walltime": "00:01:00",
                },
                "executable": "/path/to/make_hgrid.exe",
            },
            "run_dir": str(tmp_path),
            "input_grid_file": str(tmp_path / "input" / "input_grid_file"),
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
    return make_hgrid.MakeHgrid(config=config_file, batch=True)


# Driver tests


def test_MakeHgrid(driverobj):
    assert isinstance(driverobj, make_hgrid.MakeHgrid)


def test_MakeHgrid_dry_run(config_file):
    with patch.object(make_hgrid, "dryrun") as dryrun:
        driverobj = make_hgrid.MakeHgrid(config=config_file, batch=True, dry_run=True)
    assert driverobj._dry_run is True
    dryrun.assert_called_once_with()


def test_MakeHgrid_input_file(driverobj):
    path = Path(driverobj._driver_config["input_grid_file"])
    assert not driverobj.input_file().ready()
    path.parent.mkdir()
    path.touch()
    assert driverobj.input_file().ready()


def test_MakeHgrid_provisioned_run_directory(driverobj):
    with patch.multiple(
        driverobj,
        input_file=D,
        runscript=D,
    ) as mocks:
        driverobj.provisioned_run_directory()
    for m in mocks:
        mocks[m].assert_called_once_with()


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


def test_MakeHgrid__runcmd(driverobj):
    cmd = driverobj._runcmd
    input_file_path = driverobj._driver_config["input_grid_file"]
    assert cmd == f"/path/to/make_hgrid.exe {input_file_path}"


def test_MakeHgrid__runscript_path(driverobj):
    assert driverobj._runscript_path == driverobj._rundir / "runscript.make_hgrid"


def test_MakeHgrid__taskname(driverobj):
    assert driverobj._taskname("foo") == "make_hgrid foo"


def test_MakeHgrid__validate(driverobj):
    driverobj._validate()  # pylint: disable=missing-function-docstring,protected-access,redefined-outer-name
