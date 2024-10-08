# pylint: disable=missing-function-docstring,protected-access,redefined-outer-name
"""
FV3 driver tests.
"""
import datetime as dt
import logging
from pathlib import Path
from unittest.mock import DEFAULT as D
from unittest.mock import patch

import yaml
from iotaa import asset, external, refs
from pytest import fixture, mark

from uwtools.drivers.driver import Driver
from uwtools.drivers.fv3 import FV3
from uwtools.logging import log
from uwtools.scheduler import Slurm
from uwtools.tests.support import logged, regex_logged

# Fixtures


@fixture
def config(tmp_path):
    return {
        "fv3": {
            "domain": "global",
            "execution": {
                "batchargs": {
                    "walltime": "00:02:00",
                },
                "executable": str(tmp_path / "fv3"),
                "mpicmd": "srun",
            },
            "field_table": {
                "base_file": "/path/to/field_table_to_copy",
            },
            "lateral_boundary_conditions": {
                "interval_hours": 1,
                "offset": 0,
                "path": str(tmp_path / "f{forecast_hour}"),
            },
            "length": 1,
            "namelist": {
                "update_values": {
                    "namsfc": {
                        "FNZORC": "igbp",
                    },
                },
            },
            "rundir": str(tmp_path),
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
    return FV3(config=config, cycle=cycle, batch=True)


@fixture
def truetask():
    @external
    def true():
        yield "true"
        yield asset(True, lambda: True)

    return true


# Tests


@mark.parametrize(
    "method",
    [
        "_run_resources",
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
    ],
)
def test_FV3(method):
    assert getattr(FV3, method) is getattr(Driver, method)


def test_FV3_boundary_files(driverobj):
    ns = (0, 1)
    links = [driverobj.rundir / "INPUT" / f"gfs_bndy.tile7.{n:03d}.nc" for n in ns]
    assert not any(link.is_file() for link in links)
    for n in ns:
        (driverobj.rundir / f"f{n}").touch()
    driverobj.boundary_files()
    assert all(link.is_symlink() for link in links)


def test_FV3_diag_table(driverobj):
    src = driverobj.rundir / "diag_table.in"
    src.touch()
    driverobj._config["diag_table"] = src
    dst = driverobj.rundir / "diag_table"
    assert not dst.is_file()
    driverobj.diag_table()
    assert dst.is_file()


def test_FV3_diag_table_warn(caplog, driverobj):
    driverobj.diag_table()
    assert logged(caplog, "No 'diag_table' defined in config")


def test_FV3_driver_name(driverobj):
    assert driverobj.driver_name() == FV3.driver_name() == "fv3"


def test_FV3_field_table(driverobj):
    src = driverobj.rundir / "field_table.in"
    src.touch()
    dst = driverobj.rundir / "field_table"
    assert not dst.is_file()
    driverobj._config["field_table"] = {"base_file": str(src)}
    driverobj.field_table()
    assert dst.is_file()


@mark.parametrize(
    "key,task,test",
    [("files_to_copy", "files_copied", "is_file"), ("files_to_link", "files_linked", "is_symlink")],
)
def test_FV3_files_copied_and_linked(config, cycle, key, task, test, tmp_path):
    atm, sfc = "gfs.t%sz.atmanl.nc", "gfs.t%sz.sfcanl.nc"
    atm_cfg_dst, sfc_cfg_dst = [x % "{{ cycle.strftime('%H') }}" for x in [atm, sfc]]
    atm_cfg_src, sfc_cfg_src = [str(tmp_path / (x + ".in")) for x in [atm_cfg_dst, sfc_cfg_dst]]
    config["fv3"].update({key: {atm_cfg_dst: atm_cfg_src, sfc_cfg_dst: sfc_cfg_src}})
    path = tmp_path / "config.yaml"
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(config, f)
    driverobj = FV3(config=path, cycle=cycle, batch=True)
    atm_dst, sfc_dst = [tmp_path / (x % cycle.strftime("%H")) for x in [atm, sfc]]
    assert not any(dst.is_file() for dst in [atm_dst, sfc_dst])
    atm_src, sfc_src = [Path(str(x) + ".in") for x in [atm_dst, sfc_dst]]
    for src in (atm_src, sfc_src):
        src.touch()
    getattr(driverobj, task)()
    assert all(getattr(dst, test)() for dst in [atm_dst, sfc_dst])


@mark.parametrize("base_file_exists", [True, False])
def test_FV3_model_configure(base_file_exists, caplog, driverobj):
    log.setLevel(logging.DEBUG)
    src = driverobj.rundir / "model_configure.in"
    if base_file_exists:
        with open(src, "w", encoding="utf-8") as f:
            yaml.dump({}, f)
    dst = driverobj.rundir / "model_configure"
    assert not dst.is_file()
    driverobj._config["model_configure"] = {"base_file": src}
    driverobj.model_configure()
    if base_file_exists:
        assert dst.is_file()
    else:
        assert not dst.is_file()
        assert regex_logged(caplog, f"{src}: State: Not Ready (external asset)")


def test_FV3_namelist_file(caplog, driverobj):
    log.setLevel(logging.DEBUG)
    src = driverobj.rundir / "input.nml.in"
    with open(src, "w", encoding="utf-8") as f:
        yaml.dump({}, f)
    dst = driverobj.rundir / "input.nml"
    assert not dst.is_file()
    driverobj._config["namelist_file"] = {"base_file": src}
    path = Path(refs(driverobj.namelist_file()))
    assert logged(caplog, f"Wrote config to {path}")
    assert dst.is_file()


def test_FV3_namelist_file_fails_validation(caplog, driverobj):
    log.setLevel(logging.DEBUG)
    driverobj._config["namelist"]["update_values"]["namsfc"]["foo"] = None
    path = Path(refs(driverobj.namelist_file()))
    assert not path.exists()
    assert logged(caplog, f"Failed to validate {path}")
    assert logged(caplog, "  None is not of type 'array', 'boolean', 'number', 'string'")


def test_FV3_namelist_file_missing_base_file(caplog, driverobj):
    log.setLevel(logging.DEBUG)
    base_file = str(Path(driverobj.config["rundir"], "missing.nml"))
    driverobj._config["namelist"]["base_file"] = base_file
    path = Path(refs(driverobj.namelist_file()))
    assert not path.exists()
    assert regex_logged(caplog, "missing.nml: State: Not Ready (external asset)")


@mark.parametrize("domain", ("global", "regional"))
def test_FV3_provisioned_rundir(domain, driverobj):
    driverobj._config["domain"] = domain
    with patch.multiple(
        driverobj,
        boundary_files=D,
        diag_table=D,
        field_table=D,
        files_copied=D,
        files_linked=D,
        model_configure=D,
        namelist_file=D,
        restart_directory=D,
        runscript=D,
    ) as mocks:
        driverobj.provisioned_rundir()
    excluded = ["boundary_files"] if domain == "global" else []
    for m in mocks:
        if m in excluded:
            mocks[m].assert_not_called()
        else:
            mocks[m].assert_called_once_with()


def test_FV3_restart_directory(driverobj):
    path = driverobj.rundir / "RESTART"
    assert not path.is_dir()
    driverobj.restart_directory()
    assert path.is_dir()


def test_FV3_runscript(driverobj):
    with patch.object(driverobj, "_runscript") as runscript:
        driverobj.runscript()
        runscript.assert_called_once()
        args = ("envcmds", "envvars", "execution", "scheduler")
        types = [list, dict, list, Slurm]
        assert [type(runscript.call_args.kwargs[x]) for x in args] == types


def test_FV3_taskname(driverobj):
    assert driverobj.taskname("foo") == "20240201 18Z fv3 foo"
