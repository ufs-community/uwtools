# pylint: disable=missing-function-docstring,protected-access,redefined-outer-name
"""
EsgGrid driver tests.
"""
from unittest.mock import DEFAULT as D
from unittest.mock import patch

import f90nml  # type: ignore
import yaml
from pytest import fixture

from uwtools.drivers import esg_grid
from uwtools.scheduler import Slurm

# Driver fixtures


@fixture
def config(tmp_path):
    return {
        "esg_grid": {
            "execution": {
                "batchargs": {
                    "export": "NONE",
                    "nodes": 1,
                    "stdout": "/path/to/file",
                    "walltime": "00:02:00",
                },
                "envcmds": [
                    "module load some-module",
                    "module load esg-grid-module",
                ],
                "executable": "/path/to/esg_grid",
                "mpiargs": ["--export=ALL", "--ntasks $SLURM_CPUS_ON_NODE"],
                "mpicmd": "srun",
            },
            "namelist": {
                "update_values": {
                    "regional_grid_nml": {
                        "delx": 0.11,
                        "dely": 0.11,
                        "lx": -214,
                        "ly": -128,
                        "pazi": 0.0,
                        "plat": 38.5,
                        "plon": -97.5,
                    }
                }
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
def driverobj(config_file):
    return esg_grid.EsgGrid(config=config_file, batch=True)


# Driver tests


def test_EsgGrid(driverobj):
    assert isinstance(driverobj, esg_grid.EsgGrid)


def test_EsgGrid_dry_run(config_file):
    with patch.object(esg_grid, "dryrun") as dryrun:
        driverobj = esg_grid.EsgGrid(config=config_file, batch=True, dry_run=True)
    assert driverobj._dry_run is True
    dryrun.assert_called_once_with()


def test_EsgGrid_namelist_file(driverobj):
    dst = driverobj._rundir / "regional_grid.nml"
    assert not dst.is_file()
    driverobj.namelist_file()
    assert dst.is_file()
    assert isinstance(f90nml.read(dst), f90nml.Namelist)


def test_EsgGrid_provisioned_run_directory(driverobj):
    with patch.multiple(
        driverobj,
        namelist_file=D,
        runscript=D,
    ) as mocks:
        driverobj.provisioned_run_directory()
    for m in mocks:
        mocks[m].assert_called_once_with()


def test_EsgGrid_run_batch(driverobj):
    with patch.object(driverobj, "_run_via_batch_submission") as func:
        driverobj.run()
    func.assert_called_once_with()


def test_EsgGrid_run_local(driverobj):
    driverobj._batch = False
    with patch.object(driverobj, "_run_via_local_execution") as func:
        driverobj.run()
    func.assert_called_once_with()


def test_EsgGrid_runscript(driverobj):
    with patch.object(driverobj, "_runscript") as runscript:
        driverobj.runscript()
        runscript.assert_called_once()
        args = ("envcmds", "envvars", "execution", "scheduler")
        types = [list, dict, list, Slurm]
        assert [type(runscript.call_args.kwargs[x]) for x in args] == types


def test_EsgGrid__driver_config(driverobj):
    assert driverobj._driver_config == driverobj._config["esg_grid"]


def test_EsgGrid__runscript_path(driverobj):
    assert driverobj._runscript_path == driverobj._rundir / "runscript.esg_grid"


def test_EsgGrid__taskname(driverobj):
    assert driverobj._taskname("foo") == "esg_grid foo"


def test_EsgGrid__validate(driverobj):
    driverobj._validate()
