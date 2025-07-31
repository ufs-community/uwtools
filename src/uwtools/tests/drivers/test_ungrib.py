"""
Ungrib driver tests.
"""

from pathlib import Path
from unittest.mock import patch

import f90nml  # type: ignore[import-untyped]
from pytest import fixture, mark

from uwtools.drivers import ungrib
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
            "gribfiles": [
                str(tmp_path / "rap.t10z.wrfnatf00.grib2"),
                str(tmp_path / "rap.t10z.wrfnatf03.grib2"),
                str(tmp_path / "rap.t10z.wrfnatf06.grib2"),
            ],
            "rundir": str(tmp_path),
            "start": "2025-07-31T00:00:00",
            "step": "06:00:00",
            "stop": "2025-07-31T12:00:00",
            "vtable": str(tmp_path / "Vtable.GFS"),
        },
        "platform": {
            "account": "me",
            "scheduler": "slurm",
        },
    }


@fixture
def cycle(utc):
    return utc(2024, 2, 1, 18)


@fixture
def driverobj(config, cycle):
    return Ungrib(config=config, cycle=cycle, batch=True)


# Tests


def test_Ungrib_driver_name(driverobj):
    assert driverobj.driver_name() == Ungrib.driver_name() == "ungrib"


def test_Ungrib_gribfiles(driverobj):
    files = [Path(p) for p in driverobj._config["gribfiles"]]
    for file in files:
        file.touch()
    links = [driverobj.rundir / f"GRIBFILE.{ungrib._ext(i)}" for i in range(len(files))]
    assert not any(link.exists() for link in links)
    driverobj.gribfiles()
    assert all(link.is_symlink() for link in links)


def test_Ungrib_namelist_file(driverobj):
    dst = driverobj.rundir / "namelist.wps"
    assert not dst.is_file()
    driverobj.namelist_file()
    assert dst.is_file()
    nml = f90nml.read(dst)
    assert isinstance(nml, f90nml.Namelist)
    assert nml["share"]["interval_seconds"] == 21600
    assert nml["share"]["end_date"] == "2025-07-31_12:00:00"


def test_Ungrib_output(driverobj):
    assert driverobj.output["paths"] == [
        driverobj.rundir / f"FILE:{x}" for x in ("2025-07-31_00", "2025-07-31_06", "2025-07-31_12")
    ]


def test_Ungrib_output_step_zero(driverobj):
    ts = "2025-07-31T12:00:00"
    driverobj._config.update(start=ts, step=0, stop=ts)
    assert driverobj.output["paths"] == [driverobj.rundir / "FILE:2025-07-31_12"]


def test_Ungrib_provisioned_rundir(driverobj, ready_task):
    with patch.multiple(
        driverobj,
        gribfiles=ready_task,
        namelist_file=ready_task,
        runscript=ready_task,
        vtable=ready_task,
    ) as mocks:
        driverobj.provisioned_rundir()
    for m in mocks:
        mocks[m].assert_called_once_with()


def test_Ungrib_taskname(driverobj):
    assert driverobj.taskname("foo") == "20240201 18Z ungrib foo"


def test_Ungrib_vtable(driverobj):
    src = driverobj.rundir / "Vtable.GFS.in"
    src.touch()
    driverobj._config["vtable"] = src
    dst = driverobj.rundir / "Vtable"
    assert not dst.is_symlink()
    driverobj.vtable()
    assert dst.is_symlink()


def test_Ungrib__gribfile(driverobj):
    src = driverobj.rundir / "GRIBFILE.AAA.in"
    src.touch()
    dst = driverobj.rundir / "GRIBFILE.AAA"
    assert not dst.is_symlink()
    driverobj._gribfile(src, dst)
    assert dst.is_symlink()


@mark.parametrize("val", ["06:00:00", "06:00", "06", "6", 6])
def test_Ungrib__step(driverobj, val):
    driverobj._config["step"] = val
    assert int(driverobj._step.total_seconds()) == 21600


def test__ext():
    assert ungrib._ext(0) == "AAA"
    assert ungrib._ext(26) == "ABA"
