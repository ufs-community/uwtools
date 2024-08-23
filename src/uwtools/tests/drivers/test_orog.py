# pylint: disable=missing-function-docstring,protected-access,redefined-outer-name
"""
Orog driver tests.
"""
import logging
from pathlib import Path
from unittest.mock import DEFAULT as D
from unittest.mock import patch

from pytest import fixture, mark

from uwtools.drivers.driver import Driver
from uwtools.drivers.orog import Orog
from uwtools.logging import log
from uwtools.tests.support import regex_logged

# Fixtures


@fixture
def config(tmp_path):
    afile = tmp_path / "afile"
    afile.touch()
    return {
        "orog": {
            "old_line1_items": {
                "blat": 0,
                "efac": 0,
                "jcap": 0,
                "latb": 0,
                "lonb": 0,
                "mtnres": 1,
                "nr": 0,
                "nf1": 0,
                "nf2": 0,
            },
            "execution": {
                "batchargs": {
                    "walltime": "00:01:00",
                },
                "executable": "/path/to/orog",
            },
            "files_to_copy": {
                "foo": str(tmp_path / "foo"),
                "bar": str(tmp_path / "bar"),
            },
            "files_to_link": {
                "baz": str(tmp_path / "baz"),
                "qux": str(tmp_path / "qux"),
            },
            "grid_file": str(tmp_path / "grid_file.in"),
            "orog_file": "none",
            "rundir": str(tmp_path / "run"),
        },
        "platform": {
            "account": "me",
            "scheduler": "slurm",
        },
    }


@fixture
def driverobj(config):
    return Orog(config=config, batch=True)


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
        "taskname",
    ],
)
def test_Orog(method):
    assert getattr(Orog, method) is getattr(Driver, method)


def test_Orog_files_copied(driverobj):
    for _, src in driverobj.config["files_to_copy"].items():
        Path(src).touch()
    for dst, _ in driverobj.config["files_to_copy"].items():
        assert not (driverobj.rundir / dst).is_file()
    driverobj.files_copied()
    for dst, _ in driverobj.config["files_to_copy"].items():
        assert (driverobj.rundir / dst).is_file()


def test_Orog_files_linked(driverobj):
    for _, src in driverobj.config["files_to_link"].items():
        Path(src).touch()
    for dst, _ in driverobj.config["files_to_link"].items():
        assert not (driverobj.rundir / dst).is_file()
    driverobj.files_linked()
    for dst, _ in driverobj.config["files_to_link"].items():
        assert (driverobj.rundir / dst).is_symlink()


@mark.parametrize("exist", [True, False])
def test_Orog_grid_file_existence(caplog, driverobj, exist):
    log.setLevel(logging.DEBUG)
    grid_file = Path(driverobj.config["grid_file"])
    status = "Input grid file: State: Not Ready (external asset)"
    if exist:
        grid_file.touch()
        status = "Input grid file: State: Ready"
    driverobj.grid_file()
    assert regex_logged(caplog, status)


def test_Orog_grid_file_nonexistence(caplog, driverobj):
    log.setLevel(logging.INFO)
    driverobj._config["grid_file"] = "none"
    driverobj.grid_file()
    assert regex_logged(caplog, "Input grid file: State: Ready")


def test_Orog_input_config_file_new(driverobj):
    del driverobj._config["old_line1_items"]
    del driverobj._config["orog_file"]
    grid_file = Path(driverobj.config["grid_file"])
    grid_file.touch()
    driverobj.input_config_file()
    with open(driverobj._input_config_path, "r", encoding="utf-8") as inps:
        content = inps.readlines()
    content = [l.strip("\n") for l in content]
    assert len(content) == 3
    assert content[0] == driverobj.config["grid_file"]
    assert content[1] == ".false."
    assert content[2] == "none"


def test_Orog_input_config_file_old(driverobj):
    grid_file = Path(driverobj.config["grid_file"])
    grid_file.touch()
    driverobj.input_config_file()
    with open(driverobj._input_config_path, "r", encoding="utf-8") as inps:
        content = inps.readlines()
    content = [l.strip("\n") for l in content]
    assert len(content) == 5
    assert len(content[0].split()) == 9
    assert content[1] == driverobj.config["grid_file"]
    assert content[2] == driverobj.config.get("orog_file")
    assert content[3] == ".false."
    assert content[4] == "none"


def test_Orog_provisioned_rundir(driverobj):
    with patch.multiple(
        driverobj, files_copied=D, files_linked=D, input_config_file=D, runscript=D
    ) as mocks:
        driverobj.provisioned_rundir()
    for m in mocks:
        mocks[m].assert_called_once_with()


def test_Orog_driver_name(driverobj):
    assert driverobj.driver_name == "orog"


def test_Orog__runcmd(driverobj):
    assert driverobj._runcmd == "%s < %s" % (
        driverobj.config["execution"]["executable"],
        driverobj._input_config_path.name,
    )
