# pylint: disable=missing-function-docstring,protected-access,redefined-outer-name
"""
UPP driver tests.
"""
import datetime as dt
import logging
from pathlib import Path
from unittest.mock import DEFAULT as D
from unittest.mock import patch

import f90nml  # type: ignore
from iotaa import refs
from pytest import fixture, mark, raises

from uwtools.drivers.driver import Driver
from uwtools.drivers.upp import UPP
from uwtools.exceptions import UWNotImplementedError
from uwtools.logging import log
from uwtools.tests.support import logged, regex_logged

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
            "rundir": str(tmp_path / "run"),
        },
        "platform": {
            "account": "me",
            "scheduler": "slurm",
        },
    }


@fixture
def cycle():
    return dt.datetime(2024, 5, 6, 12)


@fixture
def driverobj(config, cycle, leadtime):
    return UPP(config=config, cycle=cycle, leadtime=leadtime, batch=True)


@fixture
def leadtime():
    return dt.timedelta(hours=24)


# Tests


@mark.parametrize(
    "method",
    [
        "_run_resources",
        "_run_via_batch_submission",
        "_run_via_local_execution",
        "_runscript",
        "_runscript_done_file",
        "_runscript_path",
        "_scheduler",
        "_validate",
        "_write_runscript",
        "output",
        "run",
        "runscript",
    ],
)
def test_UPP(method):
    assert getattr(UPP, method) is getattr(Driver, method)


def test_UPP_driver_name(driverobj):
    assert driverobj.driver_name() == UPP.driver_name() == "upp"


def test_UPP_files_copied(driverobj):
    for _, src in driverobj.config["files_to_copy"].items():
        Path(src).touch()
    for dst, _ in driverobj.config["files_to_copy"].items():
        assert not (driverobj.rundir / dst).is_file()
    driverobj.files_copied()
    for dst, _ in driverobj.config["files_to_copy"].items():
        assert (driverobj.rundir / dst).is_file()


def test_UPP_files_linked(driverobj):
    for _, src in driverobj.config["files_to_link"].items():
        Path(src).touch()
    for dst, _ in driverobj.config["files_to_link"].items():
        assert not (driverobj.rundir / dst).is_file()
    driverobj.files_linked()
    for dst, _ in driverobj.config["files_to_link"].items():
        assert (driverobj.rundir / dst).is_symlink()


def test_UPP_namelist_file(caplog, driverobj):
    log.setLevel(logging.DEBUG)
    datestr = "2024-05-05_12:00:00"
    with open(driverobj.config["namelist"]["base_file"], "w", encoding="utf-8") as f:
        print("&model_inputs datestr='%s' / &nampgb kpv=42 /" % datestr, file=f)
    dst = driverobj.rundir / "itag"
    assert not dst.is_file()
    path = Path(refs(driverobj.namelist_file()))
    assert dst.is_file()
    assert logged(caplog, f"Wrote config to {path}")
    nml = f90nml.read(dst)
    assert isinstance(nml, f90nml.Namelist)
    assert nml["model_inputs"]["datestr"] == datestr
    assert nml["model_inputs"]["grib"] == "grib2"
    assert nml["nampgb"]["kpo"] == 3
    assert nml["nampgb"]["kpv"] == 42


def test_UPP_namelist_file_fails_validation(caplog, driverobj):
    log.setLevel(logging.DEBUG)
    driverobj._config["namelist"]["update_values"]["nampgb"]["kpo"] = "string"
    del driverobj._config["namelist"]["base_file"]
    path = Path(refs(driverobj.namelist_file()))
    assert not path.exists()
    assert logged(caplog, f"Failed to validate {path}")
    assert logged(caplog, "  'string' is not of type 'integer'")


def test_UPP_namelist_file_missing_base_file(caplog, driverobj):
    log.setLevel(logging.DEBUG)
    base_file = str(Path(driverobj.config["rundir"], "missing.nml"))
    driverobj._config["namelist"]["base_file"] = base_file
    path = Path(refs(driverobj.namelist_file()))
    assert not path.exists()
    assert regex_logged(caplog, "missing.nml: State: Not Ready (external asset)")


def test_UPP_output(driverobj):
    with raises(UWNotImplementedError) as e:
        assert driverobj.output
    assert str(e.value) == "The output() method is not yet implemented for this driver"


def test_UPP_provisioned_rundir(driverobj):
    with patch.multiple(
        driverobj,
        files_copied=D,
        files_linked=D,
        namelist_file=D,
        runscript=D,
    ) as mocks:
        driverobj.provisioned_rundir()
    for m in mocks:
        mocks[m].assert_called_once_with()


def test_UPP_taskname(driverobj):
    assert driverobj.taskname("foo") == "20240507 12:00:00 upp foo"


def test_UPP__namelist_path(driverobj):
    assert driverobj._namelist_path == driverobj.rundir / "itag"


def test_UPP__runcmd(driverobj):
    assert driverobj._runcmd == "%s < itag" % driverobj.config["execution"]["executable"]
