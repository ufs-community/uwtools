"""
Ungrib driver tests.
"""

import re
from datetime import timedelta
from pathlib import Path
from unittest.mock import Mock, patch

import f90nml  # type: ignore[import-untyped]
import iotaa
from pytest import fixture, mark, raises

from uwtools.drivers import ungrib
from uwtools.drivers.ungrib import Ungrib
from uwtools.exceptions import UWConfigError

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
                str(tmp_path / "rap.t00z.wrfnatf00.grib2"),
                str(tmp_path / "rap.t00z.wrfnatf03.grib2"),
                str(tmp_path / "rap.t00z.wrfnatf06.grib2"),
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


def test_Ungrib_output_stop_precedes_start(driverobj):
    start = "2025-07-31T12:00:00"
    stop = "2025-07-31T00:00:00"
    driverobj._config.update(start=start, step=1, stop=stop)
    with raises(UWConfigError) as e:
        _ = driverobj.output
    assert str(e.value) == f"Value 'stop' ({stop}) precedes 'start' ({start})"


def test_Ungrib_output_step_is_one(driverobj):
    ts = "2025-07-31T12:00:00"
    driverobj._config.update(start=ts, step=1, stop=ts)
    assert driverobj.output["paths"] == [driverobj.rundir / "FILE:2025-07-31_12"]


def test_Ungrib_provisioned_rundir(driverobj, ready_task):
    with patch.multiple(
        driverobj,
        gribfiles=ready_task,
        namelist_file=ready_task,
        runscript=ready_task,
        vtable=ready_task,
    ):
        assert driverobj.provisioned_rundir().ready


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


def test_Ungrib__run_via_local_execution(driverobj):
    def make_output(*_args, **_kwargs):
        for path in driverobj.output["paths"]:
            path.touch()

    node = Mock(spec=iotaa.Node)
    with (
        patch.object(driverobj, "provisioned_rundir", return_value=node) as provisioned_rundir,
        patch.object(ungrib, "run_shell_cmd", side_effect=make_output) as run_shell_cmd,
    ):
        val = driverobj._run_via_local_execution()
        assert val.ready
        for path in val.ref:
            assert path.exists()
        run_shell_cmd.assert_called_once_with(
            cmd="{x} >{x}.out 2>&1".format(x=driverobj._runscript_path),
            cwd=driverobj.rundir,
            log_output=True,
        )
        provisioned_rundir.assert_called_once_with()


@mark.parametrize("val", ["06:00:00", "06:00", "06", "6", 6, timedelta(hours=6)])
def test_Ungrib__step(driverobj, val):
    driverobj._config["step"] = val
    assert int(driverobj._step.total_seconds()) == 21600


@mark.parametrize("val", [-6, 0, timedelta(hours=-1)])
def test_Ungrib__step_bad(driverobj, val):
    driverobj._config["step"] = val
    with raises(UWConfigError) as e:
        _ = driverobj._step
    assert re.match(r"Value for 'step' .* must be positive", str(e.value))


def test__ext():
    assert ungrib._ext(0) == "AAA"
    assert ungrib._ext(1) == "AAB"
    assert ungrib._ext(2) == "AAC"
    assert ungrib._ext(26) == "ABA"
    assert ungrib._ext(29) == "ABD"
