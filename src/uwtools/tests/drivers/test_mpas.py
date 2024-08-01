# pylint: disable=missing-function-docstring,protected-access,redefined-outer-name
"""
MPAS driver tests.
"""
import datetime as dt
import logging
from pathlib import Path
from unittest.mock import DEFAULT as D
from unittest.mock import patch

import f90nml  # type: ignore
import pytest
import yaml
from iotaa import refs
from pytest import fixture, raises

from uwtools.drivers import mpas
from uwtools.exceptions import UWConfigError
from uwtools.logging import log
from uwtools.scheduler import Slurm
from uwtools.tests.support import fixture_path, logged

# Fixtures


@fixture
def config(tmp_path):
    return {
        "mpas": {
            "execution": {
                "executable": "atmosphere_model",
                "batchargs": {
                    "walltime": "01:30:00",
                },
            },
            "lateral_boundary_conditions": {
                "interval_hours": 1,
                "offset": 0,
                "path": str(tmp_path / "input_files"),
            },
            "length": 1,
            "namelist": {
                "base_file": str(fixture_path("simple.nml")),
                "update_values": {
                    "nhyd_model": {"config_start_time": "12", "config_stop_time": "12"},
                },
            },
            "run_dir": str(tmp_path),
            "streams": {
                "path": str(tmp_path / "streams.atmosphere.in"),
                "values": {
                    "world": "user",
                },
            },
            "files_to_link": {
                "CAM_ABS_DATA.DBL": "src/MPAS-Model/CAM_ABS_DATA.DBL",
                "CAM_AEROPT_DATA.DBL": "src/MPAS-Model/CAM_AEROPT_DATA.DBL",
            },
        },
        "platform": {
            "account": "me",
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
def cycle():
    return dt.datetime(2024, 3, 22, 6)


@fixture
def driverobj(config_file, cycle):
    return mpas.MPAS(config=config_file, cycle=cycle, batch=True)


# Tests


def test_MPAS(driverobj):
    assert isinstance(driverobj, mpas.MPAS)


def test_MPAS_boundary_files(driverobj, cycle):
    ns = (0, 1)
    links = [
        driverobj._rundir / f"lbc.{(cycle+dt.timedelta(hours=n)).strftime('%Y-%m-%d_%H.%M.%S')}.nc"
        for n in ns
    ]
    assert not any(link.is_file() for link in links)
    infile_path = Path(driverobj._driver_config["lateral_boundary_conditions"]["path"])
    infile_path.mkdir()
    for n in ns:
        (
            infile_path / f"lbc.{(cycle+dt.timedelta(hours=n)).strftime('%Y-%m-%d_%H.%M.%S')}.nc"
        ).touch()
    driverobj.boundary_files()
    assert all(link.is_symlink() for link in links)


@pytest.mark.parametrize(
    "key,task,test",
    [("files_to_copy", "files_copied", "is_file"), ("files_to_link", "files_linked", "is_symlink")],
)
def test_MPAS_files_copied_and_linked(config, cycle, key, task, test, tmp_path):
    atm, sfc = "gfs.t%sz.atmanl.nc", "gfs.t%sz.sfcanl.nc"
    atm_cfg_dst, sfc_cfg_dst = [x % "{{ cycle.strftime('%H') }}" for x in [atm, sfc]]
    atm_cfg_src, sfc_cfg_src = [str(tmp_path / (x + ".in")) for x in [atm_cfg_dst, sfc_cfg_dst]]
    config["mpas"].update({key: {atm_cfg_dst: atm_cfg_src, sfc_cfg_dst: sfc_cfg_src}})
    path = tmp_path / "config.yaml"
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(config, f)
    driverobj = mpas.MPAS(config=path, cycle=cycle, batch=True)
    atm_dst, sfc_dst = [tmp_path / (x % cycle.strftime("%H")) for x in [atm, sfc]]
    assert not any(dst.is_file() for dst in [atm_dst, sfc_dst])
    atm_src, sfc_src = [Path(str(x) + ".in") for x in [atm_dst, sfc_dst]]
    for src in (atm_src, sfc_src):
        src.touch()
    getattr(driverobj, task)()
    assert all(getattr(dst, test)() for dst in [atm_dst, sfc_dst])


def test_MPAS_namelist_file(caplog, driverobj):
    log.setLevel(logging.DEBUG)
    dst = driverobj._rundir / "namelist.atmosphere"
    assert not dst.is_file()
    path = Path(refs(driverobj.namelist_file()))
    assert dst.is_file()
    assert logged(caplog, f"Wrote config to {path}")
    nml = f90nml.read(dst)
    assert isinstance(nml, f90nml.Namelist)


def test_MPAS_namelist_file_long_duration(caplog, config, cycle):
    log.setLevel(logging.DEBUG)
    config["mpas"]["length"] = 120
    driverobj = mpas.MPAS(config=config, cycle=cycle)
    dst = driverobj._rundir / "namelist.atmosphere"
    assert not dst.is_file()
    path = Path(refs(driverobj.namelist_file()))
    assert dst.is_file()
    assert logged(caplog, f"Wrote config to {path}")
    nml = f90nml.read(dst)
    assert isinstance(nml, f90nml.Namelist)
    assert nml["nhyd_model"]["config_run_duration"] == "5_0:00:00"


def test_MPAS_namelist_file_fails_validation(caplog, driverobj):
    log.setLevel(logging.DEBUG)
    driverobj._driver_config["namelist"]["update_values"]["nhyd_model"]["foo"] = None
    path = Path(refs(driverobj.namelist_file()))
    assert not path.exists()
    assert logged(caplog, f"Failed to validate {path}")
    assert logged(caplog, "  None is not of type 'array', 'boolean', 'number', 'string'")


def test_MPAS_namelist_missing(driverobj):
    path = driverobj._rundir / "namelist.atmosphere"
    del driverobj._driver_config["namelist"]
    with raises(UWConfigError) as e:
        assert driverobj.namelist_file()
    assert str(e.value) == ("Provide either a 'namelist' YAML block or the %s file" % path)


def test_MPAS_provisioned_run_directory(driverobj):
    with patch.multiple(
        driverobj,
        boundary_files=D,
        files_copied=D,
        files_linked=D,
        namelist_file=D,
        runscript=D,
        streams_file=D,
    ) as mocks:
        driverobj.provisioned_run_directory()
    for m in mocks:
        mocks[m].assert_called_once_with()


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
    with patch.object(driverobj, "_runscript") as runscript:
        driverobj.runscript()
        runscript.assert_called_once()
        args = ("envcmds", "envvars", "execution", "scheduler")
        types = [list, dict, list, Slurm]
        assert [type(runscript.call_args.kwargs[x]) for x in args] == types


def test_MPAS_streams(driverobj):
    src = driverobj._driver_config["streams"]["path"]
    with open(src, "w", encoding="utf-8") as f:
        f.write("Hello, {{ world }}")
    assert not (driverobj._rundir / "streams.atmosphere").is_file()
    driverobj.streams_file()
    assert (driverobj._rundir / "streams.atmosphere").is_file()


def test_MPAS__runscript_path(driverobj):
    assert driverobj._runscript_path == driverobj._rundir / "runscript.mpas"


def test_MPAS__taskname(driverobj):
    assert driverobj._taskname("foo") == "20240322 06Z mpas foo"


def test_MPAS__validate(driverobj):
    driverobj._validate()
