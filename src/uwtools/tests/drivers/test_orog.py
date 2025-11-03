"""
Orog driver tests.
"""

from pathlib import Path
from unittest.mock import patch

from pytest import fixture, mark

from uwtools.drivers.orog import Orog
from uwtools.scheduler import Slurm

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
            "files_to_link": {
                "foo": str(tmp_path / "foo"),
                "bar": str(tmp_path / "bar"),
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


def test_Orog_driver_name(driverobj):
    assert driverobj.driver_name() == Orog.driver_name() == "orog"


def test_Orog_files_linked(driverobj):
    for src in driverobj.config["files_to_link"].values():
        Path(src).touch()
    for dst in driverobj.config["files_to_link"]:
        assert not (driverobj.rundir / dst).is_file()
    driverobj.files_linked()
    for dst in driverobj.config["files_to_link"]:
        assert (driverobj.rundir / dst).is_symlink()


@mark.parametrize("exist", [True, False])
def test_Orog_grid_file_existence(driverobj, logged, exist):
    grid_file = Path(driverobj.config["grid_file"])
    status = f"Input grid file {grid_file!s}: Not ready [external asset]"
    if exist:
        grid_file.touch()
        status = f"Input grid file {grid_file!s}: Ready"
    driverobj.grid_file()
    assert logged(status)


def test_Orog_grid_file_nonexistence(driverobj, logged):
    driverobj._config["grid_file"] = "none"
    driverobj.grid_file()
    assert logged("Input grid file none: Ready")


def test_Orog_input_config_file_new(driverobj):
    del driverobj._config["old_line1_items"]
    del driverobj._config["orog_file"]
    grid_file = Path(driverobj.config["grid_file"])
    grid_file.touch()
    driverobj.input_config_file()
    content = Path(driverobj._input_config_path).read_text().strip().split("\n")
    assert len(content) == 3
    assert content[0] == "'{}'".format(driverobj.config["grid_file"])
    assert content[1] == ".false."
    assert content[2] == "none"


def test_Orog_input_config_file_old(driverobj):
    grid_file = Path(driverobj.config["grid_file"])
    grid_file.touch()
    driverobj.input_config_file()
    content = Path(driverobj._input_config_path).read_text().strip().split("\n")
    assert len(content) == 5
    assert len(content[0].split()) == 9
    assert content[1] == "'{}'".format(driverobj.config["grid_file"])
    assert content[2] == "'{}'".format(driverobj.config["orog_file"])
    assert content[3] == ".false."
    assert content[4] == "none"


def test_Orog_output(driverobj):
    assert driverobj.output == {"path": driverobj.rundir / "out.oro.nc"}


def test_Orog_provisioned_rundir(driverobj, ready_task):
    with patch.multiple(
        driverobj,
        files_copied=ready_task,
        files_hardlinked=ready_task,
        files_linked=ready_task,
        input_config_file=ready_task,
        runscript=ready_task,
    ):
        assert driverobj.provisioned_rundir().ready


def test_Orog_runscript(driverobj):
    with patch.object(driverobj, "_runscript") as runscript:
        driverobj.runscript()
        runscript.assert_called_once()
        args = ("envcmds", "envvars", "execution", "scheduler")
        types = [list, dict, list, Slurm]
        assert [type(runscript.call_args.kwargs[x]) for x in args] == types


def test_Orog__runcmd(driverobj):
    assert driverobj._runcmd == "%s < %s" % (
        driverobj.config["execution"]["executable"],
        driverobj._input_config_path.name,
    )
