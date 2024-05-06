# pylint: disable=missing-function-docstring,protected-access,redefined-outer-name
"""
Ungrib driver tests.
"""
import datetime as dt
from unittest.mock import DEFAULT as D
from unittest.mock import patch

import f90nml  # type: ignore
import yaml
from pytest import fixture

from uwtools.drivers import ungrib
from uwtools.scheduler import Slurm

# Fixtures


@fixture
def config(tmp_path):
    return {
        "ungrib": {
            "execution": {
                "batchargs": {
                    "cores": 1,
                    "walltime": "00:01:00",
                },
                "executable": str(tmp_path / "ungrib.exe"),
            },
            "gfs_files": {
                "forecast_length": 12,
                "interval_hours": 6,
                "offset": 6,
                "path": str(tmp_path / "gfs.t{cycle_hour:02d}z.pgrb2.0p25.f{forecast_hour:03d}"),
            },
            "run_dir": str(tmp_path),
            "vtable": str(tmp_path / "Vtable.GFS"),
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
    return dt.datetime(2024, 2, 1, 18)


@fixture
def driverobj(config_file, cycle):
    return ungrib.Ungrib(config=config_file, cycle=cycle, batch=True)


# Tests


def test_Ungrib(driverobj):
    assert isinstance(driverobj, ungrib.Ungrib)


def test_Ungrib_dry_run(config_file, cycle):
    with patch.object(ungrib, "dryrun") as dryrun:
        driverobj = ungrib.Ungrib(config=config_file, cycle=cycle, batch=True, dry_run=True)
    assert driverobj._dry_run is True
    dryrun.assert_called_once_with()


def test_Ungrib__gribfile(driverobj):
    src = driverobj._rundir / "GRIBFILE.AAA.in"
    src.touch()
    dst = driverobj._rundir / "GRIBFILE.AAA"
    assert not dst.is_symlink()
    driverobj._gribfile(src, dst)
    assert dst.is_symlink()


def test_Ungrib_gribfiles(driverobj, tmp_path):
    links = []
    cycle_hr = 12
    for n, forecast_hour in enumerate((6, 12, 18)):
        links = [driverobj._rundir / f"GRIBFILE.{ungrib._ext(n)}"]
        infile = tmp_path / "gfs.t{cycle_hr:02d}z.pgrb2.0p25.f{forecast_hour:03d}".format(
            cycle_hr=cycle_hr, forecast_hour=forecast_hour
        )
        infile.touch()
    assert not any(link.is_file() for link in links)
    driverobj.gribfiles()
    assert all(link.is_symlink() for link in links)


def test_Ungrib_namelist_file(driverobj):
    dst = driverobj._rundir / "namelist.wps"
    assert not dst.is_file()
    driverobj.namelist_file()
    assert dst.is_file()
    nml = f90nml.read(dst)
    assert isinstance(nml, f90nml.Namelist)
    assert nml["share"]["interval_seconds"] == 21600
    assert nml["share"]["end_date"] == "2024-02-02_06:00:00"


def test_Ungrib_provisioned_run_directory(driverobj):
    with patch.multiple(
        driverobj,
        gribfiles=D,
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
    with patch.object(driverobj, "_runscript") as runscript:
        driverobj.runscript()
        runscript.assert_called_once()
        args = ("envcmds", "envvars", "execution", "scheduler")
        types = [list, dict, list, Slurm]
        assert [type(runscript.call_args.kwargs[x]) for x in args] == types


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


def test_Ungrib__runscript_path(driverobj):
    assert driverobj._runscript_path == driverobj._rundir / "runscript.ungrib"


def test_Ungrib__taskname(driverobj):
    assert driverobj._taskname("foo") == "20240201 18Z ungrib foo"


def test_Ungrib__validate(driverobj):
    driverobj._validate()


def test__ext():
    assert ungrib._ext(0) == "AAA"
    assert ungrib._ext(26) == "ABA"
