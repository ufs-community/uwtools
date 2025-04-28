"""
UPP driver tests.
"""

import datetime as dt
from pathlib import Path
from unittest.mock import patch

import f90nml  # type: ignore[import-untyped]
from pytest import fixture, mark, raises

from uwtools.drivers.driver import Driver
from uwtools.drivers.upp import UPP
from uwtools.exceptions import UWConfigError

# Fixtures


@fixture
def config(tmp_path):
    return {
        "upp": {
            "control_file": "/path/to/postxconfig-NT.txt",
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
def cycle(utc):
    return utc(2024, 5, 6, 12)


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
        "run",
        "runscript",
    ],
)
def test_UPP(method):
    assert getattr(UPP, method) is getattr(Driver, method)


def test_UPP_driver_name(driverobj):
    assert driverobj.driver_name() == UPP.driver_name() == "upp"


def test_UPP_files_copied(driverobj):
    for src in driverobj.config["files_to_copy"].values():
        Path(src).touch()
    for dst in driverobj.config["files_to_copy"]:
        assert not (driverobj.rundir / dst).is_file()
    driverobj.files_copied()
    for dst in driverobj.config["files_to_copy"]:
        assert (driverobj.rundir / dst).is_file()


def test_UPP_files_linked(driverobj):
    for src in driverobj.config["files_to_link"].values():
        Path(src).touch()
    for dst in driverobj.config["files_to_link"]:
        assert not (driverobj.rundir / dst).is_file()
    driverobj.files_linked()
    for dst in driverobj.config["files_to_link"]:
        assert (driverobj.rundir / dst).is_symlink()


def test_UPP_namelist_file(driverobj, logged):
    datestr = "2024-05-05_12:00:00"
    base_file = Path(driverobj.config["namelist"]["base_file"])
    base_file.write_text("&model_inputs datestr='%s' / &nampgb kpv=42 /" % datestr)
    dst = driverobj.rundir / "itag"
    assert not dst.is_file()
    path = Path(driverobj.namelist_file().refs)
    assert dst.is_file()
    assert logged(f"Wrote config to {path}")
    nml = f90nml.read(dst)
    assert isinstance(nml, f90nml.Namelist)
    assert nml["model_inputs"]["datestr"] == datestr
    assert nml["model_inputs"]["grib"] == "grib2"
    assert nml["nampgb"]["kpo"] == 3
    assert nml["nampgb"]["kpv"] == 42


def test_UPP_namelist_file_fails_validation(driverobj, logged):
    driverobj._config["namelist"]["update_values"]["nampgb"]["kpo"] = "string"
    del driverobj._config["namelist"]["base_file"]
    path = Path(driverobj.namelist_file().refs)
    assert not path.exists()
    assert logged(f"Failed to validate {path}")
    assert logged("  'string' is not of type 'integer'")


def test_UPP_namelist_file_missing_base_file(driverobj, logged):
    base_file = str(Path(driverobj.config["rundir"], "missing.nml"))
    driverobj._config["namelist"]["base_file"] = base_file
    path = Path(driverobj.namelist_file().refs)
    assert not path.exists()
    assert logged("missing.nml: Not ready [external asset]")


def test_UPP_output(driverobj, tmp_path):
    fields = ["?"] * (UPP.NFIELDS - 1)
    parameters = ["?"] * UPP.NPARAMS
    # fmt: off
    control_data = [
        "2",                # number of blocks
        "1",                # number variables in 2nd block
        "2",                # number variables in 1st block
        "FOO",              # 1st block identifier
        *fields,            # 1st block fields
        *(parameters * 2) , # 1st block variable parameters
        "BAR",              # 2nd block identifier
        *fields,            # 2nd block fields
        *parameters,        # 2nd block variable parameters
    ]
    # fmt: on
    control_file = tmp_path / "postxconfig-NT.txt"
    control_file.write_text("\n".join(control_data))
    driverobj._config["control_file"] = str(control_file)
    expected = {"outputs": [driverobj.rundir / ("%s.GrbF24" % x) for x in ("FOO", "BAR")]}
    assert driverobj.output == expected


def test_UPP_output_fail(driverobj):
    with raises(UWConfigError) as e:
        assert driverobj.output
    assert str(e.value) == "Could not open UPP control file %s" % driverobj.config["control_file"]


def test_UPP_provisioned_rundir(driverobj, ready_task):
    with patch.multiple(
        driverobj,
        files_copied=ready_task,
        files_linked=ready_task,
        namelist_file=ready_task,
        runscript=ready_task,
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
