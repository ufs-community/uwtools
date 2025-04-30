"""
sfc_climo_gen driver tests.
"""

from pathlib import Path
from unittest.mock import patch

import f90nml  # type: ignore[import-untyped]
from pytest import fixture, mark

from uwtools.drivers import sfc_climo_gen
from uwtools.drivers.driver import Driver
from uwtools.drivers.sfc_climo_gen import SfcClimoGen

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
        "run",
        "runscript",
        "taskname",
    ],
)
def test_SfcClimoGen(method):
    assert getattr(SfcClimoGen, method) is getattr(Driver, method)


def test_SfcClimoGen_driver_name(driverobj):
    assert driverobj.driver_name() == SfcClimoGen.driver_name() == "sfc_climo_gen"


def test_SfcClimoGen_namelist_file(driverobj, logged, ready_task):
    dst = driverobj.rundir / "fort.41"
    assert not dst.is_file()
    with patch.object(sfc_climo_gen, "file", new=ready_task):
        path = Path(driverobj.namelist_file().refs)
    assert dst.is_file()
    assert logged(f"Wrote config to {path}")
    assert isinstance(f90nml.read(dst), f90nml.Namelist)


def test_SfcClimoGen_namelist_file_fails_validation(driverobj, logged, ready_task):
    driverobj._config["namelist"]["update_values"]["config"]["halo"] = "string"
    with patch.object(sfc_climo_gen, "file", new=ready_task):
        path = Path(driverobj.namelist_file().refs)
    assert not path.exists()
    assert logged(f"Failed to validate {path}")
    assert logged("  'string' is not of type 'integer'")


@mark.parametrize("halo", [1, None])
def test_SfcClimoGen_output(driverobj, halo):
    driverobj._config["namelist"]["update_values"]["config"]["halo"] = halo
    keys = [
        "facsf",
        "maximum_snow_albedo",
        "slope_type",
        "snowfree_albedo",
        "soil_type",
        "substrate_temperature",
        "vegetation_greenness",
        "vegetation_type",
    ]
    ns = [0, halo] if halo else [0]
    assert driverobj.output == {
        key: [driverobj.rundir / f"{key}.tile7.halo{n}.nc" for n in ns] for key in keys
    }


def test_SfcClimoGen_provisioned_rundir(driverobj, ready_task):
    with patch.multiple(
        driverobj,
        namelist_file=ready_task,
        runscript=ready_task,
    ) as mocks:
        driverobj.provisioned_rundir()
    for m in mocks:
        mocks[m].assert_called_once_with()
