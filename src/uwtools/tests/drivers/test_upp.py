# pylint: disable=missing-function-docstring,protected-access,redefined-outer-name
"""
UPP driver tests.
"""
import datetime as dt

# import f90nml  # type: ignore
import yaml
from pytest import fixture

from uwtools.drivers import upp

# from unittest.mock import DEFAULT as D
# from unittest.mock import patch


# from uwtools.scheduler import Slurm

# Fixtures


@fixture
def config(tmp_path):
    return {
        "upp": {
            "execution": {
                "batchargs": {
                    "cores": 1,
                    "walltime": "00:01:00",
                },
                "executable": str(tmp_path / "upp.exe"),
            },
            "files_to_copy": {
                "foo": str(tmp_path / "foo"),
                "bar": str(tmp_path / "bar"),
            },
            "files_to_link": {
                "baz": str(tmp_path / "baz"),
                "qux": str(tmp_path / "qux"),
            },
            "namelist": {
                "base_file": str(tmp_path / "base.nml"),
                "update_values": {
                    "model_inputs": {
                        "grib": "grib2",
                    },
                    "nampgb": {
                        "kpo": 3,
                    },
                },
            },
            "run_dir": str(tmp_path),
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
    return dt.datetime(2024, 5, 6, 12)


@fixture
def driverobj(config_file, cycle, leadtime):
    return upp.UPP(config=config_file, cycle=cycle, leadtime=leadtime, batch=True)


@fixture
def leadtime():
    return 24


# Driver tests


def test_UPP(driverobj):
    assert isinstance(driverobj, upp.UPP)


# def test_UPP_dry_run(config_file, cycle):
#     with patch.object(upp, "dryrun") as dryrun:
#         driverobj = upp.UPP(config=config_file, cycle=cycle, batch=True, dry_run=True)
#     assert driverobj._dry_run is True
#     dryrun.assert_called_once_with()


# def test_UPP__gribfile(driverobj):
#     src = driverobj._rundir / "GRIBFILE.AAA.in"
#     src.touch()
#     dst = driverobj._rundir / "GRIBFILE.AAA"
#     assert not dst.is_symlink()
#     driverobj._gribfile(src, dst)
#     assert dst.is_symlink()


# def test_UPP_gribfiles(driverobj, tmp_path):
#     links = []
#     cycle_hr = 12
#     for n, forecast_hour in enumerate((6, 12, 18)):
#         links = [driverobj._rundir / f"GRIBFILE.{upp._ext(n)}"]
#         infile = tmp_path / "gfs.t{cycle_hr:02d}z.pgrb2.0p25.f{forecast_hour:03d}".format(
#             cycle_hr=cycle_hr, forecast_hour=forecast_hour
#         )
#         infile.touch()
#     assert not any(link.is_file() for link in links)
#     driverobj.gribfiles()
#     assert all(link.is_symlink() for link in links)


# def test_UPP_namelist_file(driverobj):
#     dst = driverobj._rundir / "namelist.wps"
#     assert not dst.is_file()
#     driverobj.namelist_file()
#     assert dst.is_file()
#     nml = f90nml.read(dst)
#     assert isinstance(nml, f90nml.Namelist)
#     assert nml["share"]["interval_seconds"] == 21600
#     assert nml["share"]["end_date"] == "2024-02-02_06:00:00"


# def test_UPP_provisioned_run_directory(driverobj):
#     with patch.multiple(
#         driverobj,
#         gribfiles=D,
#         namelist_file=D,
#         runscript=D,
#         vtable=D,
#     ) as mocks:
#         driverobj.provisioned_run_directory()
#     for m in mocks:
#         mocks[m].assert_called_once_with()


# def test_UPP_run_batch(driverobj):
#     with patch.object(driverobj, "_run_via_batch_submission") as func:
#         driverobj.run()
#     func.assert_called_once_with()


# def test_UPP_run_local(driverobj):
#     driverobj._batch = False
#     with patch.object(driverobj, "_run_via_local_execution") as func:
#         driverobj.run()
#     func.assert_called_once_with()


# def test_UPP_runscript(driverobj):
#     with patch.object(driverobj, "_runscript") as runscript:
#         driverobj.runscript()
#         runscript.assert_called_once()
#         args = ("envcmds", "envvars", "execution", "scheduler")
#         types = [list, dict, list, Slurm]
#         assert [type(runscript.call_args.kwargs[x]) for x in args] == types


# def test_UPP_vtable(driverobj):
#     src = driverobj._rundir / "Vtable.GFS.in"
#     src.touch()
#     driverobj._driver_config["vtable"] = src
#     dst = driverobj._rundir / "Vtable"
#     assert not dst.is_symlink()
#     driverobj.vtable()
#     assert dst.is_symlink()


# def test_UPP__driver_config(driverobj):
#     assert driverobj._driver_config == driverobj._config["upp"]


# def test_UPP__runscript_path(driverobj):
#     assert driverobj._runscript_path == driverobj._rundir / "runscript.upp"


# def test_UPP__taskname(driverobj):
#     assert driverobj._taskname("foo") == "20240201 18Z upp foo"


# def test_UPP__validate(driverobj):
#     driverobj._validate()


# def test__ext():
#     assert upp._ext(0) == "AAA"
#     assert upp._ext(26) == "ABA"
