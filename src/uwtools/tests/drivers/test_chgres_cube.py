# pylint: disable=missing-function-docstring,protected-access,redefined-outer-name
"""
chgres_cube driver tests.
"""
import datetime as dt
import logging
from pathlib import Path
from unittest.mock import DEFAULT as D
from unittest.mock import patch

import f90nml  # type: ignore
import yaml
from iotaa import asset, external, refs
from pytest import fixture

from uwtools.drivers import chgres_cube
from uwtools.logging import log
from uwtools.scheduler import Slurm
from uwtools.tests.support import logged

# Fixtures


@fixture
def cycle():
    return dt.datetime(2024, 2, 1, 18)


@fixture
def config_file(tmp_path):
    config: dict = {
        "chgres_cube": {
            "execution": {
                "batchargs": {
                    "export": "NONE",
                    "nodes": 1,
                    "stdout": "/path/to/file",
                    "walltime": "00:02:00",
                },
                "envcmds": ["cmd1", "cmd2"],
                "executable": "/path/to/chgres_cube",
                "mpiargs": ["--export=ALL", "--ntasks $SLURM_CPUS_ON_NODE"],
                "mpicmd": "srun",
            },
            "namelist": {
                "update_values": {
                    "config": {
                        "atm_core_files_input_grid": "/path/to/file",
                        "atm_files_input_grid": "/path/to/file",
                        "atm_tracer_files_input_grid": "/path/to/file",
                        "atm_weight_file": "/path/to/file",
                        "convert_atm": True,
                        "data_dir_input_grid": "/path/to/file",
                        "external_model": "GFS",
                        "fix_dir_target_grid": "/path/to/dir",
                        "geogrid_file_input_grid": "/path/to/file",
                        "grib2_file_input_grid": "/path/to/file",
                        "mosaic_file_input_grid": "/path/to/file",
                        "mosaic_file_target_grid": "/path/to/file",
                        "sfc_files_input_grid": "/path/to/file",
                        "varmap_file": "/path/to/file",
                        "vcoord_file_target_grid": "/path/to/file",
                    }
                },
                "validate": True,
            },
            "run_dir": "/path/to/dir",
        },
        "platform": {
            "account": "me",
            "scheduler": "slurm",
        },
    }
    path = tmp_path / "config.yaml"
    config["chgres_cube"]["run_dir"] = tmp_path.as_posix()
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(config, f)
    return path


@fixture
def driverobj(config_file, cycle):
    return chgres_cube.ChgresCube(config=config_file, cycle=cycle, batch=True)


# Helpers


@external
def ready(x):
    yield x
    yield asset(x, lambda: True)


# Tests


def test_ChgresCube(driverobj):
    assert isinstance(driverobj, chgres_cube.ChgresCube)


def test_ChgresCube_namelist_file(caplog, driverobj):
    log.setLevel(logging.DEBUG)
    dst = driverobj._rundir / "fort.41"
    assert not dst.is_file()
    with patch.object(chgres_cube, "file", new=ready):
        path = Path(refs(driverobj.namelist_file()))
    assert dst.is_file()
    assert logged(caplog, f"Wrote config to {path}")
    assert isinstance(f90nml.read(dst), f90nml.Namelist)


def test_ChgresCube_namelist_file_fails_validation(caplog, driverobj):
    log.setLevel(logging.DEBUG)
    driverobj._driver_config["namelist"]["update_values"]["config"]["convert_atm"] = "string"
    with patch.object(chgres_cube, "file", new=ready):
        path = Path(refs(driverobj.namelist_file()))
    assert not path.exists()
    assert logged(caplog, f"Failed to validate {path}")
    assert logged(caplog, "  'string' is not of type 'boolean'")


def test_ChgresCube_provisioned_run_directory(driverobj):
    with patch.multiple(driverobj, namelist_file=D, runscript=D) as mocks:
        driverobj.provisioned_run_directory()
    for m in mocks:
        mocks[m].assert_called_once_with()


def test_ChgresCube_run_batch(driverobj):
    with patch.object(driverobj, "_run_via_batch_submission") as func:
        driverobj.run()
    func.assert_called_once_with()


def test_ChgresCube_run_local(driverobj):
    driverobj._batch = False
    with patch.object(driverobj, "_run_via_local_execution") as func:
        driverobj.run()
    func.assert_called_once_with()


def test_ChgresCube_runscript(driverobj):
    with patch.object(driverobj, "_runscript") as runscript:
        driverobj.runscript()
        runscript.assert_called_once()
        args = ("envcmds", "envvars", "execution", "scheduler")
        types = [list, dict, list, Slurm]
        assert [type(runscript.call_args.kwargs[x]) for x in args] == types


def test_ChgresCube__driver_config(driverobj):
    assert driverobj._driver_config == driverobj._config["chgres_cube"]


def test_ChgresCube__runscript_path(driverobj):
    assert driverobj._runscript_path == driverobj._rundir / "runscript.chgres_cube"


def test_ChgresCube__taskname(driverobj):
    assert driverobj._taskname("foo") == "20240201 18Z chgres_cube foo"


def test_ChgresCube__validate(driverobj):
    driverobj._validate()
