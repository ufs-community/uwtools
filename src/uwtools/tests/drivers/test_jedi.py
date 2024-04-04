# pylint: disable=missing-function-docstring,protected-access,redefined-outer-name
"""
JEDI driver tests.
"""
import datetime as dt
from unittest.mock import DEFAULT as D
from unittest.mock import patch

import yaml
from pytest import fixture

from uwtools.drivers import jedi
from uwtools.scheduler import Slurm
from uwtools.tests.support import fixture_path

# Fixtures


@fixture
def cycle():
    return dt.datetime(2024, 2, 1, 18)


# Driver fixtures


@fixture
def config(tmp_path):
    return {
        "jedi": {
            "execution": {
                "batchargs": {
                    "export": "NONE",
                    "nodes": 1,
                    "stdout": "/path/to/file",
                    "walltime": "00:02:00",
                },
                "envcmds": ["cmd1", "cmd2"],
                "executable": "/scratch2/BMC/zrtrr/Naureen.Bharwani/build/bin/qg_forecast.x",
                "mpiargs": ["--export=ALL", "--ntasks $SLURM_CPUS_ON_NODE"],
                "mpicmd": "srun",
            },
            "configuration_file": {
                "base_file": str(fixture_path("jedi.yaml")),
                "update_values": {"jedi": {}},
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
def driverobj(config_file, cycle):
    return jedi.JEDI(config_file=config_file, cycle=cycle, batch=True)


# Driver tests


def test_JEDI(driverobj):
    assert isinstance(driverobj, jedi.JEDI)


def test_JEDI_dry_run(config_file, cycle):
    with patch.object(jedi, "dryrun") as dryrun:
        driverobj = jedi.JEDI(config_file=config_file, cycle=cycle, batch=True, dry_run=True)
    assert driverobj._dry_run is True
    dryrun.assert_called_once_with()


def test_JEDI_provisioned_run_directory(driverobj):
    with patch.multiple(
        driverobj,
        files_copied=D,
        files_linked=D,
        runscript=D,
        # validate_only=D,
        yaml_file=D,
    ) as mocks:
        driverobj.provisioned_run_directory()
    for m in mocks:
        mocks[m].assert_called_once_with()


def test_JEDI_runscript(driverobj):
    with patch.object(driverobj, "_runscript") as runscript:
        driverobj.runscript()
        runscript.assert_called_once()
        args = ("envcmds", "envvars", "execution", "scheduler")
        types = [list, dict, list, Slurm]
        assert [type(runscript.call_args.kwargs[x]) for x in args] == types


def test_JEDI_validate_only(config_file, cycle, driverobj):
    driverobj.validate_only()


def test_JEDI_yaml_file(driverobj):
    pass
    # src = driverobj._rundir / "input.yaml"


def test_JEDI__driver_config(driverobj):
    assert driverobj._driver_config == driverobj._config["jedi"]


def test_JEDI__runscript_path(driverobj):
    assert driverobj._runscript_path == driverobj._rundir / "runscript.jedi"


def test_JEDI__taskname(driverobj):
    assert driverobj._taskname("foo") == "20240201 18Z jedi foo"
