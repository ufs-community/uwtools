# pylint: disable=missing-function-docstring,protected-access,redefined-outer-name
"""
MPASInit driver tests.
"""
import datetime as dt
import logging
from pathlib import Path
from unittest.mock import DEFAULT as D
from unittest.mock import patch

import f90nml  # type: ignore
from iotaa import refs
from pytest import fixture, mark

from uwtools.drivers.mpas_base import MPASBase
from uwtools.drivers.mpas_init import MPASInit
from uwtools.logging import log
from uwtools.tests.drivers.test_mpas import streams_file
from uwtools.tests.support import fixture_path, logged, regex_logged

# Fixtures


@fixture
def config(tmp_path):
    return {
        "mpas_init": {
            "boundary_conditions": {
                "interval_hours": 1,
                "length": 1,
                "offset": 0,
                "path": str(tmp_path / "input_path"),
            },
            "execution": {
                "batchargs": {
                    "walltime": "01:30:00",
                },
                "executable": "mpas_init",
            },
            "files_to_link": {
                "CAM_ABS_DATA.DBL": "src/MPAS-Model/CAM_ABS_DATA.DBL",
                "CAM_AEROPT_DATA.DBL": "src/MPAS-Model/CAM_AEROPT_DATA.DBL",
                "GENPARM.TBL": "src/MPAS-Model/GENPARM.TBL",
                "LANDUSE.TBL": "src/MPAS-Model/LANDUSE.TBL",
                "OZONE_DAT.TBL": "src/MPAS-Model/OZONE_DAT.TBL",
                "OZONE_LAT.TBL": "src/MPAS-Model/OZONE_LAT.TBL",
                "OZONE_PLEV.TBL": "src/MPAS-Model/OZONE_PLEV.TBL",
                "RRTMG_LW_DATA": "src/MPAS-Model/RRTMG_LW_DATA",
                "RRTMG_LW_DATA.DBL": "src/MPAS-Model/RRTMG_LW_DATA.DBL",
                "RRTMG_SW_DATA": "src/MPAS-Model/RRTMG_SW_DATA",
                "RRTMG_SW_DATA.DBL": "src/MPAS-Model/RRTMG_SW_DATA.DBL",
                "SOILPARM.TBL": "src/MPAS-Model/SOILPARM.TBL",
                "VEGPARM.TBL": "src/MPAS-Model/VEGPARM.TBL",
            },
            "namelist": {
                "base_file": str(fixture_path("simple.nml")),
                "update_values": {
                    "nhyd_model": {"config_start_time": "12", "config_stop_time": "12"},
                },
            },
            "rundir": str(tmp_path),
            "streams": {
                "input": {
                    "filename_template": "conus.static.nc",
                    "input_interval": "initial_only",
                    "mutable": False,
                    "type": "input",
                },
                "output": {
                    "filename_template": "conus.init.nc",
                    "files": ["stream_list.atmosphere.output"],
                    "mutable": False,
                    "output_interval": "initial_only",
                    "streams": ["stream1", "stream2"],
                    "type": "output",
                    "vars": ["v1", "v2"],
                    "var_arrays": ["va1", "va2"],
                    "var_structs": ["vs1", "vs2"],
                },
            },
        },
        "platform": {
            "account": "me",
            "scheduler": "slurm",
        },
    }


@fixture
def cycle():
    return dt.datetime(2024, 2, 1, 18)


@fixture
def driverobj(config, cycle):
    return MPASInit(config=config, cycle=cycle, batch=True)


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
        "_taskname",
        "_validate",
        "_write_runscript",
        "run",
        "runscript",
        "streams_file",
    ],
)
def test_MPASInit(method):
    assert getattr(MPASInit, method) is getattr(MPASBase, method)


def test_MPASInit_boundary_files(cycle, driverobj):
    ns = (0, 1)
    links = [
        driverobj.rundir / f"FILE:{(cycle+dt.timedelta(hours=n)).strftime('%Y-%m-%d_%H')}"
        for n in ns
    ]
    assert not any(link.is_file() for link in links)
    input_path = Path(driverobj.config["boundary_conditions"]["path"])
    input_path.mkdir()
    for n in ns:
        (input_path / f"FILE:{(cycle+dt.timedelta(hours=n)).strftime('%Y-%m-%d_%H')}").touch()
    driverobj.boundary_files()
    assert all(link.is_symlink() for link in links)


@mark.parametrize(
    "key,task,test",
    [("files_to_copy", "files_copied", "is_file"), ("files_to_link", "files_linked", "is_symlink")],
)
def test_MPASInit_files_copied_and_linked(config, cycle, key, task, test, tmp_path):
    atm, sfc = "gfs.t%sz.atmanl.nc", "gfs.t%sz.sfcanl.nc"
    atm_cfg_dst, sfc_cfg_dst = [x % "{{ cycle.strftime('%H') }}" for x in [atm, sfc]]
    atm_cfg_src, sfc_cfg_src = [str(tmp_path / (x + ".in")) for x in [atm_cfg_dst, sfc_cfg_dst]]
    config["mpas_init"].update({key: {atm_cfg_dst: atm_cfg_src, sfc_cfg_dst: sfc_cfg_src}})
    driverobj = MPASInit(config=config, cycle=cycle, batch=True)
    atm_dst, sfc_dst = [tmp_path / (x % cycle.strftime("%H")) for x in [atm, sfc]]
    assert not any(dst.is_file() for dst in [atm_dst, sfc_dst])
    atm_src, sfc_src = [Path(str(x) + ".in") for x in [atm_dst, sfc_dst]]
    for src in (atm_src, sfc_src):
        src.touch()
    getattr(driverobj, task)()
    assert all(getattr(dst, test)() for dst in [atm_dst, sfc_dst])


def test_MPASInit_namelist_contents(cycle, driverobj):
    dst = driverobj.rundir / "namelist.init_atmosphere"
    assert not dst.is_file()
    driverobj.namelist_file()
    assert dst.is_file()
    nml = f90nml.read(dst)
    stop_time = cycle + dt.timedelta(hours=1)
    f = "%Y-%m-%d_%H:00:00"
    assert nml["nhyd_model"]["config_start_time"] == cycle.strftime(f)
    assert nml["nhyd_model"]["config_stop_time"] == stop_time.strftime(f)


def test_MPASInit_namelist_file(caplog, driverobj):
    log.setLevel(logging.DEBUG)
    dst = driverobj.rundir / "namelist.init_atmosphere"
    assert not dst.is_file()
    path = Path(refs(driverobj.namelist_file()))
    assert dst.is_file()
    assert logged(caplog, f"Wrote config to {path}")
    assert isinstance(f90nml.read(dst), f90nml.Namelist)


def test_MPASInit_namelist_file_fails_validation(caplog, driverobj):
    log.setLevel(logging.DEBUG)
    driverobj._config["namelist"]["update_values"]["nhyd_model"]["foo"] = None
    path = Path(refs(driverobj.namelist_file()))
    assert not path.exists()
    assert logged(caplog, f"Failed to validate {path}")
    assert logged(caplog, "  None is not of type 'array', 'boolean', 'number', 'string'")


def test_MPASInit_namelist_file_missing_base_file(caplog, driverobj):
    log.setLevel(logging.DEBUG)
    base_file = str(Path(driverobj.config["rundir"], "missing.nml"))
    driverobj._config["namelist"]["base_file"] = base_file
    path = Path(refs(driverobj.namelist_file()))
    assert not path.exists()
    assert regex_logged(caplog, "missing.nml: State: Not Ready (external asset)")


def test_MPASInit_provisioned_rundir(driverobj):
    with patch.multiple(
        driverobj,
        boundary_files=D,
        files_copied=D,
        files_linked=D,
        namelist_file=D,
        runscript=D,
        streams_file=D,
    ) as mocks:
        driverobj.provisioned_rundir()
    for m in mocks:
        mocks[m].assert_called_once_with()


def test_MPASInit__driver_name(driverobj):
    assert driverobj._driver_name == "mpas_init"


def test_MPASInit_streams_file(config, driverobj):
    streams_file(config, driverobj, "mpas_init")


def test_MPASInit__streams_fn(driverobj):
    assert driverobj._streams_fn == "streams.init_atmosphere"
