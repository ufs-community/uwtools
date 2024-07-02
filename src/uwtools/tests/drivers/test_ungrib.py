# pylint: disable=missing-function-docstring,protected-access,redefined-outer-name
"""
Ungrib driver tests.
"""
import datetime as dt
from unittest.mock import DEFAULT as D
from unittest.mock import patch

import f90nml  # type: ignore
from pytest import fixture, mark

from uwtools.drivers import ungrib
from uwtools.drivers.driver import Driver
from uwtools.drivers.ungrib import Ungrib

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
            "rundir": str(tmp_path),
            "vtable": str(tmp_path / "Vtable.GFS"),
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
    return Ungrib(config=config, cycle=cycle, batch=True)


# Tests


@mark.parametrize(
    "method",
    [
        "_driver_config",
        "_resources",
        "_run_via_batch_submission",
        "_run_via_local_execution",
        "_runcmd",
        "_runscript",
        "_runscript_done_file",
        "_runscript_path",
        "_scheduler",
        "_validate",
        "_write_runscript",
        "run",
        "runscript",
    ],
)
def test_Ungrib(method):
    assert getattr(Ungrib, method) is getattr(Driver, method)


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


def test_Ungrib_provisioned_rundir(driverobj):
    with patch.multiple(
        driverobj,
        gribfiles=D,
        namelist_file=D,
        runscript=D,
        vtable=D,
    ) as mocks:
        driverobj.provisioned_rundir()
    for m in mocks:
        mocks[m].assert_called_once_with()


def test_Ungrib_vtable(driverobj):
    src = driverobj._rundir / "Vtable.GFS.in"
    src.touch()
    driverobj._driver_config["vtable"] = src
    dst = driverobj._rundir / "Vtable"
    assert not dst.is_symlink()
    driverobj.vtable()
    assert dst.is_symlink()


def test_Ungrib__driver_name(driverobj):
    assert driverobj._driver_name == "ungrib"


def test_Ungrib__gribfile(driverobj):
    src = driverobj._rundir / "GRIBFILE.AAA.in"
    src.touch()
    dst = driverobj._rundir / "GRIBFILE.AAA"
    assert not dst.is_symlink()
    driverobj._gribfile(src, dst)
    assert dst.is_symlink()


def test_Ungrib__taskname(driverobj):
    assert driverobj._taskname("foo") == "20240201 18Z ungrib foo"


def test__ext():
    assert ungrib._ext(0) == "AAA"
    assert ungrib._ext(26) == "ABA"
