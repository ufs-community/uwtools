# pylint: disable=missing-function-docstring,protected-access,redefined-outer-name
"""
Ungrib driver tests.
"""
import datetime as dt
from pathlib import Path
from unittest.mock import DEFAULT as D
from unittest.mock import PropertyMock, patch

import yaml
from pytest import fixture

from uwtools.drivers import ungrib

# Fixtures


@fixture
def cycle():
    return dt.datetime(2024, 2, 1, 18)


# Driver fixtures


@fixture
def config(tmp_path):
    return {
        "ungrib": {
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
    return ungrib.Ungrib(config_file=config_file, cycle=cycle, batch=True)


# Driver tests


def test_Ungrib(driverobj):
    assert isinstance(driverobj, ungrib.Ungrib)


def test_Ungrib_dry_run(config_file, cycle):
    with patch.object(ungrib, "dryrun") as dryrun:
        driverobj = ungrib.Ungrib(config_file=config_file, cycle=cycle, batch=True, dry_run=True)
    assert driverobj._dry_run is True
    dryrun.assert_called_once_with()


def test_Ungrib_namelist_wps(driverobj):
    src = driverobj._rundir / "namelist.wps.in"
    with open(src, "w", encoding="utf-8") as f:
        yaml.dump({}, f)
    dst = driverobj._rundir / "namelist.wps"
    assert not dst.is_file()
    driverobj._driver_config["namelist_file"] = {"base_file": src}
    driverobj.namelist_wps()
    assert dst.is_file()


def test_Ungrib_provisioned_run_directory(driverobj):
    with patch.multiple(
        driverobj,
        gribfile_aaa=D,
        namelist_wps=D,
        runscript=D,
        vtable=D,
    ) as mocks:
        driverobj.provisioned_run_directory()
    for m in mocks:
        mocks[m].assert_called_once_with()


def test_Ungrib_run_batch(driverobj):
    with patch.object(driverobj, "_run_via_batch_submission") as func:
        driverobj.run()
    func.assert_called_once_with()


def test_Ungrib_run_local(driverobj):
    driverobj._batch = False
    with patch.object(driverobj, "_run_via_local_execution") as func:
        driverobj.run()
    func.assert_called_once_with()


def test_Ungrib_runscript(driverobj):
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


def test_Ungrib__run_via_batch_submission(driverobj):
    runscript = driverobj._runscript_path
    with patch.object(driverobj, "provisioned_run_directory") as prd:
        with patch.object(ungrib.Ungrib, "_scheduler", new_callable=PropertyMock) as scheduler:
            driverobj._run_via_batch_submission()
            scheduler().submit_job.assert_called_once_with(
                runscript=runscript, submit_file=Path(f"{runscript}.submit")
            )
        prd.assert_called_once_with()


def test_Ungrib__driver_config(driverobj):
    assert driverobj._driver_config == driverobj._config["ungrib"]


def test_Ungrib__resources(driverobj):
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


def test_Ungrib__runscript_path(driverobj):
    assert driverobj._runscript_path == driverobj._rundir / "runscript"


def test_Ungrib__taskanme(driverobj):
    assert driverobj._taskname("foo") == "20240201 18Z Ungrib foo"


def test_Ungrib__validate(driverobj):
    driverobj._validate()
