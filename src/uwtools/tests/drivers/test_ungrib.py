# pylint: disable=missing-function-docstring,protected-access,redefined-outer-name
"""
Ungrib driver tests.
"""
import datetime as dt
from unittest.mock import DEFAULT as D
from unittest.mock import patch

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
            "execution": {
                "mpicmd": "srun",
                "batchargs": {
                    "cores": 1,
                    "walltime": "00:01:00",
                },
                "executable": str(tmp_path / "ungrib.exe"),
            },
            "gfs_file": str(tmp_path / "gfs.t12z.pgrb2.0p25.f000"),
            "run_dir": str(tmp_path),
            "vtable": str(tmp_path / "Vtable.GFS"),
        },
        "platform": {
            "account": "wrfruc",
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


def test_Ungrib_gribfile_aaa(driverobj):
    src = driverobj._rundir / "GRIBFILE.AAA.in"
    src.touch()
    driverobj._driver_config["gfs_file"] = src
    dst = driverobj._rundir / "GRIBFILE.AAA"
    assert not dst.is_symlink()
    driverobj.gribfile_aaa()
    assert dst.is_symlink()


def test_Ungrib_namelist_file(driverobj):
    dst = driverobj._rundir / "namelist.wps"
    assert not dst.is_file()
    driverobj.namelist_file()
    assert dst.is_file()


def test_Ungrib_provisioned_run_directory(driverobj):
    with patch.multiple(
        driverobj,
        gribfile_aaa=D,
        namelist_file=D,
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
    dst = driverobj._rundir / "runscript.ungrib"
    assert not dst.is_file()
    driverobj._driver_config["execution"].update(
        {
            "batchargs": {"walltime": "00:01:00"},
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
    assert "#SBATCH --time=00:01:00" in lines
    # Check environment commands:
    assert "cmd1" in lines
    assert "cmd2" in lines
    # Check execution:
    assert "test $? -eq 0 && touch %s/done" % driverobj._rundir


def test_Ungrib_vtable(driverobj):
    src = driverobj._rundir / "Vtable.GFS.in"
    src.touch()
    driverobj._driver_config["vtable"] = src
    dst = driverobj._rundir / "Vtable"
    assert not dst.is_symlink()
    driverobj.vtable()
    assert dst.is_symlink()


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
    assert driverobj._runscript_path == driverobj._rundir / "runscript.ungrib"


def test_Ungrib__taskanme(driverobj):
    assert driverobj._taskname("foo") == "20240201 18Z ungrib foo"


def test_Ungrib__validate(driverobj):
    driverobj._validate()
