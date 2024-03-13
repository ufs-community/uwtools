# pylint: disable=missing-function-docstring,protected-access,redefined-outer-name
"""
MPAS driver tests.
"""
import datetime as dt
from pathlib import Path
from unittest.mock import DEFAULT as D
from unittest.mock import PropertyMock, patch

# import pytest
import yaml
from pytest import fixture

from uwtools.drivers import mpas_init

# Fixtures


@fixture
def cycle():
    return dt.datetime(2024, 2, 1, 18)


# Driver fixtures


@fixture
def config(tmp_path):
    return {
        "mpas_init": {
            "domain": "global",
            "execution": {"executable": "fv3"},
            "lateral_boundary_conditions": {
                "interval_hours": 1,
                "offset": 0,
                "path": str(tmp_path / "f{forecast_hour}"),
            },
            "length": 1,
            "run_dir": str(tmp_path),
        }
    }


@fixture
def config_file(config, tmp_path):
    path = tmp_path / "config.yaml"
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(config, f)
    return path


@fixture
def driverobj(config_file, cycle):
    return mpas_init.MPASInit(config_file=config_file, cycle=cycle, batch=True)


# Driver tests


def test_MPASInit(driverobj):
    assert isinstance(driverobj, mpas_init.MPASInit)


def test_MPASInit_dry_run(config_file, cycle):
    with patch.object(mpas_init, "dryrun") as dryrun:
        driverobj = mpas_init.MPASInit(
            config_file=config_file, cycle=cycle, batch=True, dry_run=True
        )
    assert driverobj._dry_run is True
    dryrun.assert_called_once_with()


def test_MPASInit_namelist_file(driverobj):
    src = driverobj._rundir / "namelist.atmosphere.in"
    with open(src, "w", encoding="utf-8") as f:
        yaml.dump({}, f)
    dst = driverobj._rundir / "namelist.atmosphere"
    assert not dst.is_file()
    driverobj._driver_config["namelist_file"] = {"base_file": src}
    driverobj.namelist_file()
    assert dst.is_file()


def test_MPASInit_provisioned_run_directory(driverobj):
    with patch.multiple(
        driverobj,
        namelist_file=D,
        runscript=D,
    ) as mocks:
        driverobj.provisioned_run_directory()
    for m in mocks:
        mocks[m].assert_called_once_with()


def test_MPASInit_run_batch(driverobj):
    with patch.object(driverobj, "_run_via_batch_submission") as func:
        driverobj.run()
    func.assert_called_once_with()


def test_MPASInit_run_local(driverobj):
    driverobj._batch = False
    with patch.object(driverobj, "_run_via_local_execution") as func:
        driverobj.run()
    func.assert_called_once_with()


def test_Init_runscript(driverobj):
    dst = driverobj._rundir / "runscript"
    assert not dst.is_file()
    driverobj._driver_config["execution"].update(
        {
            "batchargs": {"walltime": "01:10:00"},
            "envcmds": ["cmd1", "cmd2"],
            "mpicmd": "runit",
            "threads": 8,
        }
    )
    driverobj._config["platform"] = {"account": "me", "scheduler": "slurm"}
    driverobj.runscript()
    with open(dst, "r", encoding="utf-8") as f:
        lines = f.read().split("\n")
    # Check directives:
    assert "#SBATCH --account=me" in lines
    assert "#SBATCH --time=01:10:00" in lines
    # Check environment commands:
    assert "cmd1" in lines
    assert "cmd2" in lines
    # Check execution:
    # assert "runit mpas" in lines
    assert "test $? -eq 0 && touch %s/done" % driverobj._rundir


def test_MPASInit__run_via_batch_submission(driverobj):
    runscript = driverobj._runscript_path
    with patch.object(driverobj, "provisioned_run_directory") as prd:
        with patch.object(mpas_init.MPASInit, "_scheduler", new_callable=PropertyMock) as scheduler:
            driverobj._run_via_batch_submission()
            scheduler().submit_job.assert_called_once_with(
                runscript=runscript, submit_file=Path(f"{runscript}.submit")
            )
        prd.assert_called_once_with()


def test_MPASInit__run_via_local_execution(driverobj):
    with patch.object(driverobj, "provisioned_run_directory") as prd:
        with patch.object(mpas_init, "execute") as execute:
            driverobj._run_via_local_execution()
            execute.assert_called_once_with(
                cmd="{x} >{x}.out 2>&1".format(x=driverobj._runscript_path),
                cwd=driverobj._rundir,
                log_output=True,
            )
        prd.assert_called_once_with()


def test_MPASInit__driver_config(driverobj):
    assert driverobj._driver_config == driverobj._config["mpas_init"]


def test_MPASInit__resources(driverobj):
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


def test_MPASInit__runscript_path(driverobj):
    assert driverobj._runscript_path == driverobj._rundir / "runscript"


def test_MPASInit__taskanme(driverobj):
    assert driverobj._taskname("foo") == "20240201 18Z MPASInit foo"


def test_MPASInit__validate(driverobj):
    driverobj._validate()
