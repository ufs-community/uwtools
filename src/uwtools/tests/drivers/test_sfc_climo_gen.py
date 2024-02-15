# pylint: disable=missing-function-docstring,protected-access,redefined-outer-name
"""
sfc_climo_gen driver tests.
"""
from unittest.mock import DEFAULT as D
from unittest.mock import patch

import f90nml  # type: ignore
import yaml
from iotaa import asset, external
from pytest import fixture

from uwtools.drivers import sfc_climo_gen


@fixture
def config():
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
                "executable": "/path/to/exe",
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
                }
            },
            "run_dir": "/path/to/dir",
        },
        "platform": {
            "account": "zrtrr",
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
    return sfc_climo_gen.SfcClimoGen(config_file=config_file, batch=True)


# Driver tests


def test_SfcClimoGen(driverobj):
    assert isinstance(driverobj, sfc_climo_gen.SfcClimoGen)


def test_SfcClimoGen_dry_run(config_file):
    with patch.object(sfc_climo_gen, "dryrun") as dryrun:
        driverobj = sfc_climo_gen.SfcClimoGen(config_file=config_file, batch=True, dry_run=True)
    assert driverobj._dry_run is True
    dryrun.assert_called_once_with()


def test_SfcClimoGen_namelist_file(driverobj, tmp_path):
    @external
    def ready(x):
        yield x
        yield asset(x, lambda: True)

    driverobj._rundir = tmp_path
    dst = driverobj._rundir / "fort.41"
    assert not dst.is_file()
    with patch.object(sfc_climo_gen, "file", new=ready):
        driverobj.namelist_file()
    assert dst.is_file()
    assert isinstance(f90nml.read(dst), f90nml.Namelist)


def test_SfcClimoGen_provisioned_run_directory(driverobj):
    with patch.multiple(
        driverobj,
        namelist_file=D,
        runscript=D,
    ) as mocks:
        driverobj.provisioned_run_directory()
    for m in mocks:
        mocks[m].assert_called_once_with()
