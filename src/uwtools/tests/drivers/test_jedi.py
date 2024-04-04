# pylint: disable=missing-function-docstring,protected-access,redefined-outer-name
"""
JEDI driver tests.
"""
import datetime as dt
from unittest.mock import DEFAULT as D
from unittest.mock import patch

import yaml
from iotaa import asset, external
from pytest import fixture

from uwtools.drivers import jedi 
from uwtools.scheduler import Slurm

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
            "executable": "/scratch2/BMC/zrtrr/Naureen.Bharwani/build/bin/qg_forecast.x", # str(tmp_path / "jedi.exe"),
            "mpiargs": ["--export=ALL", "--ntasks $SLURM_CPUS_ON_NODE"],
            "mpicmd": "srun",
        },
        "configuration_file": {
            "update_values": {
                "jedi": {
                    
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
def driverobj(config_file, cycle):
    return jedi.JEDI(config_file=config_file, cycle=cycle, batch=True)


# Driver tests


def test_JEDI(driverobj):
    assert isinstance(driverobj, jedi.JEDI)


def test_JEDI_validate_only(config_file, cycle, driverobj):
    driverobj.validate_only()
