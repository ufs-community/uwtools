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

config: dict = {
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
            }
        },
        "run_dir": "/path/to/dir",
    },
    "platform": {
        "account": "me",
        "scheduler": "slurm",
    },
}


@fixture
def config_file(tmp_path):
    path = tmp_path / "config.yaml"
    config["sfc_climo_gen"]["run_dir"] = tmp_path.as_posix()
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


def test_SfcClimoGen_namelist_file(driverobj):
    @external
    def ready(x):
        yield x
        yield asset(x, lambda: True)

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


def test_SfcClimoGen_run_batch(driverobj):
    with patch.object(driverobj, "_run_via_batch_submission") as func:
        driverobj.run()
    func.assert_called_once_with()


def test_SfcClimoGen_run_local(driverobj):
    driverobj._batch = False
    with patch.object(driverobj, "_run_via_local_execution") as func:
        driverobj.run()
    func.assert_called_once_with()


def test_SfcClimoGen_runscript(driverobj):
    dst = driverobj._rundir / "runscript.sfc_climo_gen"
    assert not dst.is_file()
    driverobj.runscript()
    with open(dst, "r", encoding="utf-8") as f:
        lines = f.read().split("\n")
    # Check directives:
    assert "#SBATCH --account=me" in lines
    assert "#SBATCH --time=00:02:00" in lines
    # Check environment commands:
    assert "cmd1" in lines
    assert "cmd2" in lines
    # Check execution:
    assert "srun --export=ALL --ntasks $SLURM_CPUS_ON_NODE /path/to/sfc_climo_gen" in lines
    assert "test $? -eq 0 && touch %s/done" % driverobj._rundir


def test_SfcClimoGen__driver_config(driverobj):
    assert driverobj._driver_config == driverobj._config["sfc_climo_gen"]


def test_SfcClimoGen__resources(driverobj):
    account = "me"
    scheduler = "slurm"
    walltime = "01:10:00"
    driverobj._driver_config["execution"].update({"batchargs": {"walltime": walltime}})
    driverobj._config["platform"] = {"account": account, "scheduler": scheduler}
    assert driverobj._resources == {
        "account": account,
        "rundir": driverobj._rundir,
        "scheduler": scheduler,
        "walltime": walltime,
    }


def test_SfcClimoGen__runscript_path(driverobj):
    assert driverobj._runscript_path == driverobj._rundir / "runscript.sfc_climo_gen"


def test_SfcClimoGen__taskanme(driverobj):
    assert driverobj._taskname("foo") == "sfc_climo_gen foo"


def test_SfcClimoGen__validate(driverobj):
    driverobj._validate()
