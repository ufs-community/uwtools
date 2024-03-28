# pylint: disable=missing-function-docstring,protected-access,redefined-outer-name
"""
MPASInit driver tests.
"""
import datetime as dt
from pathlib import Path
from unittest.mock import DEFAULT as D
from unittest.mock import patch

import f90nml  # type: ignore
import pytest
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
            "execution": {"executable": "mpas_init"},
            "boundary_conditions": {
                "interval_hours": 1,
                "offset": 0,
                "path": str(tmp_path / "f{forecast_hour}"),
            },
            "length": 1,
            "namelist": {
                "update_values": {
                    "nhyd_model": {"config_start_time": "12", "config_stop_time": "12"},
                },
            },
            "run_dir": str(tmp_path),
            "streams": {
                "path": str(tmp_path / "streams.init_atmosphere.in"),
                "values": {
                    "world": "Emily",
                },
            },
            "ungrib_files": {
                "path": str(tmp_path),
            },
            "files_to_link": {
                "CAM_ABS_DATA.DBL": "src/MPAS-Model/CAM_ABS_DATA.DBL",
                "CAM_AEROPT_DATA.DBL": "src/MPAS-Model/CAM_AEROPT_DATA.DBL",
                "GENPARM.TBL": "src/MPAS-Model/GENPARM.TBL",
                "LANDUSE.TBL": "src/MPAS-Model/LANDUSE.TBL",
                "OZONE_DAT.TBL": "src/MPAS-Model/OZONE_DAT.TBL",
                "OZONE_LAT.TBL": "src/MPAS-Model/OZONE_LAT.TBL",
                "OZONE_PLEV.TBL": "src/MPAS-Model/COZONE_PLEV.TBL",
                "RRTMG_LW_DATA": "src/MPAS-Model/RRTMG_LW_DATA",
                "RRTMG_LW_DATA.DBL": "src/MPAS-Model/RRTMG_LW_DATA.DBL",
                "RRTMG_SW_DATA": "src/MPAS-Model/RRTMG_SW_DATA",
                "RRTMG_SW_DATA.DBL": "src/MPAS-Model/RRTMG_SW_DATA.DBL",
                "SOILPARM.TBL": "src/MPAS-Model/SOILPARM.TBL",
                "VEGPARM.TBL": "src/MPAS-Model/VEGPARM.TBL",
            },
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
    return mpas_init.MPASInit(config=config_file, cycle=cycle, batch=True)


# Driver tests


def test_MPASInit(driverobj):
    assert isinstance(driverobj, mpas_init.MPASInit)


def test_MPASInit_boundary_files(driverobj, cycle, tmp_path):
    ns = (0, 1)
    links = [driverobj._rundir / f"FILE:{(cycle+dt.timedelta(hours=n)).strftime('%Y-%m-%d_%H')}" for n in ns]
    assert not any(link.is_file() for link in links)
    for n in ns:
        (tmp_path / f"FILE:{(cycle+dt.timedelta(hours=n)).strftime('%Y-%m-%d_%H')}").touch()
    driverobj.boundary_files()
    assert all(link.is_symlink() for link in links)


def test_MPASInit_dry_run(config_file, cycle):
    with patch.object(mpas_init, "dryrun") as dryrun:
        driverobj = mpas_init.MPASInit(config=config_file, cycle=cycle, batch=True, dry_run=True)
    assert driverobj._dry_run is True
    dryrun.assert_called_once_with()


@pytest.mark.parametrize(
    "key,task,test",
    [("files_to_copy", "files_copied", "is_file"), ("files_to_link", "files_linked", "is_symlink")],
)
def test_MPASInit_files_copied(config, cycle, key, task, test, tmp_path):
    atm, sfc = "gfs.t%sz.atmanl.nc", "gfs.t%sz.sfcanl.nc"
    atm_cfg_dst, sfc_cfg_dst = [x % "{{ cycle.strftime('%H') }}" for x in [atm, sfc]]
    atm_cfg_src, sfc_cfg_src = [str(tmp_path / (x + ".in")) for x in [atm_cfg_dst, sfc_cfg_dst]]
    config["mpas_init"].update({key: {atm_cfg_dst: atm_cfg_src, sfc_cfg_dst: sfc_cfg_src}})
    path = tmp_path / "config.yaml"
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(config, f)
    driverobj = mpas_init.MPASInit(config=path, cycle=cycle, batch=True)
    atm_dst, sfc_dst = [tmp_path / (x % cycle.strftime("%H")) for x in [atm, sfc]]
    assert not any(dst.is_file() for dst in [atm_dst, sfc_dst])
    atm_src, sfc_src = [Path(str(x) + ".in") for x in [atm_dst, sfc_dst]]
    for src in (atm_src, sfc_src):
        src.touch()
    getattr(driverobj, task)()
    assert all(getattr(dst, test)() for dst in [atm_dst, sfc_dst])


def test_MPASInit_init_executable(driverobj):
    src = driverobj._rundir / "init_atmosphere_model.in"
    src.touch()
    driverobj._driver_config["init_atmosphere_model"] = src
    dst = driverobj._rundir / "init_atmosphere_model"
    assert not dst.is_symlink()
    driverobj.init_executable_linked()
    assert dst.is_symlink()


def test_MPASInit_namelist_init(driverobj):
    dst = driverobj._rundir / "namelist.init_atmosphere"
    assert not dst.is_file()
    driverobj.namelist_init()
    assert dst.is_file()
    assert isinstance(f90nml.read(dst), f90nml.Namelist)


def test_MPASInit_provisioned_run_directory(driverobj):
    with patch.multiple(
        driverobj,
        boundary_files=D,
        init_executable_linked=D,
        files_copied=D,
        files_linked=D,
        namelist_init=D,
        runscript=D,
        streams_init=D,
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


def test_MPASInit_runscript(driverobj):
    dst = driverobj._rundir / "runscript.mpas_init"
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


def test_MPASInit_streams_init(driverobj):
    src = driverobj._driver_config["streams"]["path"]
    with open(src, "w", encoding="utf-8") as f:
        f.write("Hello, {{ world }}")
    assert not (driverobj._rundir / "streams.init_atmosphere").is_file()
    driverobj.streams_init()
    assert (driverobj._rundir / "streams.init_atmosphere").is_file()


def test_MPASInit__driver_config(driverobj):
    assert driverobj._driver_config == driverobj._config["mpas_init"]


def test_MPASInit__resources(driverobj):
    account = "me"
    scheduler = "slurm"
    walltime = "00:01:00"
    driverobj._driver_config["execution"].update({"batchargs": {"walltime": walltime}})
    driverobj._config["platform"] = {"account": account, "scheduler": scheduler}
    assert driverobj._resources == {
        "account": account,
        "rundir": driverobj._rundir,
        "scheduler": scheduler,
        "walltime": walltime,
    }


def test_MPASInit__runscript_path(driverobj):
    assert driverobj._runscript_path == driverobj._rundir / "runscript.mpas_init"


def test_MPASInit__taskanme(driverobj):
    assert driverobj._taskname("foo") == "20240201 18Z mpas-init foo"


def test_MPASInit__validate(driverobj):
    driverobj._validate()
