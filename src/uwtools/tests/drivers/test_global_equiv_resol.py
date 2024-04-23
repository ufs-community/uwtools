# pylint: disable=missing-function-docstring,protected-access,redefined-outer-name
"""
global_equiv_resol driver tests.
"""
import logging
from pathlib import Path
from unittest.mock import DEFAULT as D
from unittest.mock import patch

import yaml
from pytest import fixture

from uwtools.drivers import global_equiv_resol
from uwtools.logging import log
from uwtools.scheduler import Slurm
from uwtools.tests.support import regex_logged

# Driver fixtures


@fixture
def config(tmp_path):
    return {
        "global_equiv_resol": {
            "execution": {
                "batchargs": {
                    "cores": 1,
                    "walltime": "00:01:00",
                },
                "executable": "/path/to/global_equiv_resol.exe",
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
    return global_equiv_resol.GlobalEquivResol(config=config_file, batch=True)


# Driver tests


def test_GlobalEquivResol(driverobj):
    assert isinstance(driverobj, global_equiv_resol.GlobalEquivResol)


def test_GlobalEquivResol_dry_run(config_file):
    with patch.object(global_equiv_resol, "dryrun") as dryrun:
        driverobj = global_equiv_resol.GlobalEquivResol(
            config=config_file, batch=True, dry_run=True
        )
    assert driverobj._dry_run is True
    dryrun.assert_called_once_with()


def test_GlobalEquivResol_input_file(caplog, driverobj):
    log.setLevel(logging.INFO)
    path = Path(driverobj._driver_config["input_grid_file"])
    driverobj.input_file()
    assert regex_logged(caplog, "State: Pending (EXTERNAL)")
    path.parent.mkdir()
    path.touch()
    caplog.clear()
    driverobj.input_file()
    assert regex_logged(caplog, "State: Ready")


def test_GlobalEquivResol_provisioned_run_directory(driverobj):
    with patch.multiple(
        driverobj,
        input_file=D,
        runscript=D,
    ) as mocks:
        driverobj.provisioned_run_directory()
    for m in mocks:
        mocks[m].assert_called_once_with()


def test_GlobalEquivResol_run_batch(driverobj):
    with patch.object(driverobj, "_run_via_batch_submission") as func:
        driverobj.run()
    func.assert_called_once_with()


def test_GlobalEquivResol_run_local(driverobj):
    driverobj._batch = False
    with patch.object(driverobj, "_run_via_local_execution") as func:
        driverobj.run()
    func.assert_called_once_with()


def test_GlobalEquivResol_runscript(driverobj):
    with patch.object(driverobj, "_runscript") as runscript:
        driverobj.runscript()
        runscript.assert_called_once()
        args = ("envcmds", "envvars", "execution", "scheduler")
        types = [list, dict, list, Slurm]
        assert [type(runscript.call_args.kwargs[x]) for x in args] == types


def test_GlobalEquivResol__driver_config(driverobj):
    assert driverobj._driver_config == driverobj._config["global_equiv_resol"]


def test_GlobalEquivResol__runcmd(driverobj):
    cmd = driverobj._runcmd
    input_file_path = driverobj._driver_config["input_grid_file"]
    assert cmd == f"/path/to/global_equiv_resol.exe {input_file_path}"


def test_GlobalEquivResol__runscript_path(driverobj):
    assert driverobj._runscript_path == driverobj._rundir / "runscript.global_equiv_resol"


def test_GlobalEquivResol__taskname(driverobj):
    assert driverobj._taskname("foo") == "global_equiv_resol foo"


def test_GlobalEquivResol__validate(driverobj):
    driverobj._validate()
