# pylint: disable=missing-function-docstring,protected-access,redefined-outer-name
"""
sfc_climo_gen driver tests.
"""
import logging
from pathlib import Path
from unittest.mock import patch

import f90nml  # type: ignore
import iotaa
from pytest import fixture, mark, raises

from uwtools.drivers import sfc_climo_gen
from uwtools.drivers.driver import Driver
from uwtools.drivers.sfc_climo_gen import SfcClimoGen
from uwtools.exceptions import UWNotImplementedError
from uwtools.logging import log
from uwtools.tests.support import logged

# Fixtures


@fixture
def config(tmp_path):
    return {
        "sfc_climo_gen": {
            "execution": {
                "batchargs": {
                    "export": "NONE",
                    "nodes": 1,
                    "stdout": "/path/to/file",
                    "walltime": "00:02:00",
                },
                "envcmds": ["cmd1", "cmd2"],
                "executable": "/path/to/sfc_climo_gen",
                "mpiargs": ["--export=ALL", "--ntasks $SLURM_CPUS_ON_NODE"],
                "mpicmd": "srun",
            },
            "namelist": {
                "update_values": {
                    "config": {
                        "halo": 4,
                        "input_facsf_file": "/path/to/file",
                        "input_maximum_snow_albedo_file": "/path/to/file",
                        "input_slope_type_file": "/path/to/file",
                        "input_snowfree_albedo_file": "/path/to/file",
                        "input_soil_type_file": "/path/to/file",
                        "input_substrate_temperature_file": "/path/to/file",
                        "input_vegetation_greenness_file": "/path/to/file",
                        "input_vegetation_type_file": "/path/to/file",
                        "maximum_snow_albedo_method": "bilinear",
                        "mosaic_file_mdl": "/path/to/file",
                        "orog_dir_mdl": "/path/to/dir",
                        "orog_files_mdl": ["C403_oro_data.tile7.halo4.nc"],
                        "snowfree_albedo_method": "bilinear",
                        "vegetation_greenness_method": "bilinear",
                    }
                },
                "validate": True,
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
    return SfcClimoGen(config=config, batch=True)


# Tests


@mark.parametrize(
    "method",
    [
        "_run_resources",
        "_run_via_batch_submission",
        "_run_via_local_execution",
        "_runcmd",
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
def test_SfcClimoGen(method):
    assert getattr(SfcClimoGen, method) is getattr(Driver, method)


def test_SfcClimoGen_driver_name(driverobj):
    assert driverobj.driver_name() == SfcClimoGen.driver_name() == "sfc_climo_gen"


def test_SfcClimoGen_namelist_file(caplog, driverobj, ready_task):
    log.setLevel(logging.DEBUG)
    dst = driverobj.rundir / "fort.41"
    assert not dst.is_file()
    with patch.object(sfc_climo_gen, "file", new=ready_task):
        path = Path(iotaa.refs(driverobj.namelist_file()))
    assert dst.is_file()
    assert logged(caplog, f"Wrote config to {path}")
    assert isinstance(f90nml.read(dst), f90nml.Namelist)


def test_SfcClimoGen_namelist_file_fails_validation(caplog, driverobj, ready_task):
    log.setLevel(logging.DEBUG)
    driverobj._config["namelist"]["update_values"]["config"]["halo"] = "string"
    with patch.object(sfc_climo_gen, "file", new=ready_task):
        path = Path(iotaa.refs(driverobj.namelist_file()))
    assert not path.exists()
    assert logged(caplog, f"Failed to validate {path}")
    assert logged(caplog, "  'string' is not of type 'integer'")


def test_SfcClimoGen_output(driverobj):
    with raises(UWNotImplementedError) as e:
        assert driverobj.output
    assert str(e.value) == "The output() method is not yet implemented for this driver"


def test_SfcClimoGen_provisioned_rundir(driverobj, ready_task):
    with patch.multiple(
        driverobj,
        namelist_file=ready_task,
        runscript=ready_task,
    ) as mocks:
        driverobj.provisioned_rundir()
    for m in mocks:
        mocks[m].assert_called_once_with()
