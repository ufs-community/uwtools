# pylint: disable=missing-function-docstring,protected-access,redefined-outer-name
"""
MPAS driver tests.
"""
import datetime as dt
from pathlib import Path
from unittest.mock import DEFAULT as D
from unittest.mock import PropertyMock, patch

import pytest
import yaml
from pytest import fixture

from uwtools.drivers import mpas

# Fixtures


@fixture
def cycle():
    return dt.datetime(2024, 2, 1, 18)


# Driver fixtures


@fixture
def config(tmp_path):
    return {
        "mpas": {
            "domain": "global",
            "execution": {"executable": "mpas"},
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
    return mpas.MPAS(config_file=config_file, cycle=cycle, batch=True)


# Driver tests


def test_MPAS(driverobj):
    assert isinstance(driverobj, mpas.MPAS)


def test_MPAS_dry_run(config_file, cycle):
    with patch.object(mpas, "dryrun") as dryrun:
        driverobj = mpas.MPAS(config_file=config_file, cycle=cycle, batch=True, dry_run=True)
    assert driverobj._dry_run is True
    dryrun.assert_called_once_with()


def test_MPAS_boundary_files(driverobj):
    ns = (0, 1)
    links = [driverobj._rundir / "INPUT" / f"gfs_bndy.tile7.{n:03d}.nc" for n in ns]
    assert not any(link.is_file() for link in links)
    for n in ns:
        (driverobj._rundir / f"f{n}").touch()
    driverobj.boundary_files()
    assert all(link.is_symlink() for link in links)


@pytest.mark.parametrize(
    "key,task,test",
    [("files_to_copy", "files_copied", "is_file"), ("files_to_link", "files_linked", "is_symlink")],
)
def test_MPAS_files_copied(config, cycle, key, task, test, tmp_path):
    atm, sfc = "gfs.t%sz.atmanl.nc", "gfs.t%sz.sfcanl.nc"
    atm_cfg_dst, sfc_cfg_dst = [x % "{{ cycle.strftime('%H') }}" for x in [atm, sfc]]
    atm_cfg_src, sfc_cfg_src = [str(tmp_path / (x + ".in")) for x in [atm_cfg_dst, sfc_cfg_dst]]
    config["mpas"].update({key: {atm_cfg_dst: atm_cfg_src, sfc_cfg_dst: sfc_cfg_src}})
    path = tmp_path / "config.yaml"
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(config, f)
    driverobj = mpas.MPAS(config_file=path, cycle=cycle, batch=True)
    atm_dst, sfc_dst = [tmp_path / (x % cycle.strftime("%H")) for x in [atm, sfc]]
    assert not any(dst.is_file() for dst in [atm_dst, sfc_dst])
    atm_src, sfc_src = [Path(str(x) + ".in") for x in [atm_dst, sfc_dst]]
    for src in (atm_src, sfc_src):
        src.touch()
    getattr(driverobj, task)()
    assert all(getattr(dst, test)() for dst in [atm_dst, sfc_dst])


def test_MPAS_model_configure(driverobj):
    src = driverobj._rundir / "model_configure.in"
    with open(src, "w", encoding="utf-8") as f:
        yaml.dump({}, f)
    dst = driverobj._rundir / "model_configure"
    assert not dst.is_file()
    driverobj._driver_config["model_configure"] = {"base_file": src}
    driverobj.model_configure()
    assert dst.is_file()


def test_MPAS_namelist_file(driverobj):
    src = driverobj._rundir / "input.nml.in"
    with open(src, "w", encoding="utf-8") as f:
        yaml.dump({}, f)
    dst = driverobj._rundir / "input.nml"
    assert not dst.is_file()
    driverobj._driver_config["namelist_file"] = {"base_file": src}
    driverobj.namelist_file()
    assert dst.is_file()


def test_MPAS_provisioned_run_directory(driverobj):
    with patch.multiple(
        driverobj,
        boundary_files=D,
        files_copied=D,
        files_linked=D,
        model_configure=D,
        namelist_file=D,
        restart_directory=D,
        runscript=D,
    ) as mocks:
        driverobj.provisioned_run_directory()
    for m in mocks:
        mocks[m].assert_called_once_with()


def test_MPAS_restart_directory(driverobj):
    path = driverobj._rundir / "RESTART"
    assert not path.is_dir()
    driverobj.restart_directory()
    assert path.is_dir()


def test_MPAS_run_batch(driverobj):
    with patch.object(driverobj, "_run_via_batch_submission") as func:
        driverobj.run()
    func.assert_called_once_with()


def test_MPAS_run_local(driverobj):
    driverobj._batch = False
    with patch.object(driverobj, "_run_via_local_execution") as func:
        driverobj.run()
    func.assert_called_once_with()


def test_MPAS_runscript(driverobj):
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
    # Check environment variables:
    assert "export ESMF_RUNTIME_COMPLIANCECHECK=OFF:depth=4" in lines
    assert "export KMP_AFFINITY=scatter" in lines
    assert "export MPI_TYPE_DEPTH=20" in lines
    assert "export OMP_NUM_THREADS=8" in lines
    assert "export OMP_STACKSIZE=512m" in lines
    # Check environment commands:
    assert "cmd1" in lines
    assert "cmd2" in lines
    # Check execution:
    assert "runit mpas" in lines
    assert "test $? -eq 0 && touch %s/done" % driverobj._rundir


def test_MPAS__run_via_batch_submission(driverobj):
    runscript = driverobj._runscript_path
    with patch.object(driverobj, "provisioned_run_directory") as prd:
        with patch.object(mpas.MPAS, "_scheduler", new_callable=PropertyMock) as scheduler:
            driverobj._run_via_batch_submission()
            scheduler().submit_job.assert_called_once_with(
                runscript=runscript, submit_file=Path(f"{runscript}.submit")
            )
        prd.assert_called_once_with()


def test_MPAS__run_via_local_execution(driverobj):
    with patch.object(driverobj, "provisioned_run_directory") as prd:
        with patch.object(mpas, "execute") as execute:
            driverobj._run_via_local_execution()
            execute.assert_called_once_with(
                cmd="{x} >{x}.out 2>&1".format(x=driverobj._runscript_path),
                cwd=driverobj._rundir,
                log_output=True,
            )
        prd.assert_called_once_with()


def test_MPAS__driver_config(driverobj):
    assert driverobj._driver_config == driverobj._config["mpas"]


def test_MPAS__resources(driverobj):
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


def test_MPAS__runscript_path(driverobj):
    assert driverobj._runscript_path == driverobj._rundir / "runscript"


def test_MPAS__taskanme(driverobj):
    assert driverobj._taskname("foo") == "20240201 18Z MPAS foo"


def test_MPAS__validate(driverobj):
    driverobj._validate()