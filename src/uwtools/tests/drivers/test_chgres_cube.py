# pylint: disable=missing-function-docstring,protected-access,redefined-outer-name
"""
chgres_cube driver tests.
"""
import datetime as dt
from unittest.mock import DEFAULT as D
from unittest.mock import patch

import f90nml  # type: ignore
import yaml
from iotaa import asset, external
from pytest import fixture

from uwtools.drivers import chgres_cube

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


# Fixtures


@fixture
def cycle():
    return dt.datetime(2024, 2, 1, 18)


@fixture
def config_file(tmp_path):
    path = tmp_path / "config.yaml"
    config["chgres_cube"]["run_dir"] = tmp_path.as_posix()
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(config, f)
    return path


@fixture
def driverobj(config_file, cycle):
    return chgres_cube.ChgresCube(config_file=config_file, cycle=cycle, batch=True)


# Driver tests


def test_ChgresCube(driverobj):
    assert isinstance(driverobj, chgres_cube.ChgresCube)


def test_ChgresCube_dry_run(config_file, cycle):
    with patch.object(chgres_cube, "dryrun") as dryrun:
        driverobj = chgres_cube.ChgresCube(
            config_file=config_file, cycle=cycle, batch=True, dry_run=True
        )
    assert driverobj._dry_run is True
    dryrun.assert_called_once_with()


def test_ChgresCube_namelist_file(driverobj):
    @external
    def ready(x):
        yield x
        yield asset(x, lambda: True)

    dst = driverobj._rundir / "fort.41"
    assert not dst.is_file()
    with patch.object(chgres_cube, "file", new=ready):
        driverobj._driver_config["namelist"]["update_values"]["config"] = {
            "data_dir_input_grid": "/path/to/file",
            "atm_files_input_grid": "/path/to/file",
            "grib2_file_input_grid": "/path/to/file",
            "sfc_files_input_grid": "/path/to/file",
            "mosaic_file_target_grid": "/path/to/file",
            "varmap_file": "/path/to/file",
            "vcoord_file_target_grid": "/path/to/file",
        }
        driverobj.namelist_file()
    assert dst.is_file()
    assert isinstance(f90nml.read(dst), f90nml.Namelist)


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
    dst = driverobj._rundir / "runscript.chgres_cube"
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
    assert "srun --export=ALL --ntasks $SLURM_CPUS_ON_NODE /path/to/chgres_cube" in lines
    assert "test $? -eq 0 && touch %s/done" % driverobj._rundir


def test_ChgresCube__driver_config(driverobj):
    assert driverobj._driver_config == driverobj._config["chgres_cube"]


def test_ChgresCube__resources(driverobj):
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


def test_ChgresCube__runscript_path(driverobj):
    assert driverobj._runscript_path == driverobj._rundir / "runscript.chgres_cube"


def test_ChgresCube__taskname(driverobj):
    assert driverobj._taskname("foo") == "20240201 18Z chgres_cube foo"


def test_ChgresCube__validate(driverobj):
    driverobj._validate()
