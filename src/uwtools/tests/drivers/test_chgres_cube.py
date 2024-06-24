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
from iotaa import refs
from pytest import fixture, mark

from uwtools.drivers.chgres_cube import ChgresCube
from uwtools.drivers.driver import Driver
from uwtools.logging import log
from uwtools.scheduler import Slurm
from uwtools.tests.support import logged, regex_logged

# Fixtures


@fixture
def cycle():
    return dt.datetime(2024, 2, 1, 18)


@fixture
def config(tmp_path):
    afile = tmp_path / "afile"
    afile.touch()
    return {
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
                        "atm_core_files_input_grid": str(afile),
                        "atm_files_input_grid": str(afile),
                        "atm_tracer_files_input_grid": str(afile),
                        "atm_weight_file": str(afile),
                        "convert_atm": True,
                        "data_dir_input_grid": str(afile),
                        "external_model": "GFS",
                        "fix_dir_target_grid": "/path/to/dir",
                        "geogrid_file_input_grid": str(afile),
                        "grib2_file_input_grid": str(afile),
                        "mosaic_file_input_grid": str(afile),
                        "mosaic_file_target_grid": str(afile),
                        "sfc_files_input_grid": str(afile),
                        "varmap_file": str(afile),
                        "vcoord_file_target_grid": str(afile),
                    }
                },
                "validate": True,
            },
            "run_dir": str(tmp_path),
        },
        "platform": {
            "account": "me",
            "scheduler": "slurm",
        },
    }


@fixture
def driverobj(config, cycle):
    return ChgresCube(config=config, cycle=cycle, batch=True)


# Tests


@mark.parametrize(
    "method",
    [
        "_driver_config",
        "_resources",
        "_run_via_batch_submission",
        "_run_via_local_execution",
        "_runcmd",
        "_runscript",
        "_runscript_done_file",
        "_runscript_path",
        "_scheduler",
        "_validate",
        "_write_runscript",
        "run",
    ],
)
def test_ChgresCube(method):
    assert getattr(ChgresCube, method) is getattr(Driver, method)


def test_ChgresCube_namelist_file(caplog, driverobj):
    log.setLevel(logging.DEBUG)
    dst = driverobj._rundir / "fort.41"
    assert not dst.is_file()
    path = Path(refs(driverobj.namelist_file()))
    assert dst.is_file()
    assert logged(caplog, f"Wrote config to {path}")
    assert isinstance(f90nml.read(dst), f90nml.Namelist)


def test_ChgresCube_namelist_file_fails_validation(caplog, driverobj):
    log.setLevel(logging.DEBUG)
    driverobj._driver_config["namelist"]["update_values"]["config"]["convert_atm"] = "string"
    path = Path(refs(driverobj.namelist_file()))
    assert not path.exists()
    assert logged(caplog, f"Failed to validate {path}")
    assert logged(caplog, "  'string' is not of type 'boolean'")


def test_ChgresCube_namelist_file_missing_base_file(caplog, driverobj):
    log.setLevel(logging.DEBUG)
    base_file = str(Path(driverobj._driver_config["run_dir"]) / "missing.nml")
    driverobj._driver_config["namelist"]["base_file"] = base_file
    path = Path(refs(driverobj.namelist_file()))
    assert not path.exists()
    assert regex_logged(caplog, "missing.nml: State: Not Ready (external asset)")


def test_ChgresCube_provisioned_run_directory(driverobj):
    with patch.multiple(driverobj, namelist_file=D, runscript=D) as mocks:
        driverobj.provisioned_run_directory()
    for m in mocks:
        mocks[m].assert_called_once_with()


def test_ChgresCube_runscript(driverobj):
    with patch.object(driverobj, "_runscript") as runscript:
        driverobj.runscript()
        runscript.assert_called_once()
        args = ("envcmds", "envvars", "execution", "scheduler")
        types = [list, dict, list, Slurm]
        assert [type(runscript.call_args.kwargs[x]) for x in args] == types


def test_ChgresCube__driver_name(driverobj):
    assert driverobj._driver_name == "chgres_cube"


def test_ChgresCube__taskname(driverobj):
    assert driverobj._taskname("foo") == "20240201 18Z chgres_cube foo"
