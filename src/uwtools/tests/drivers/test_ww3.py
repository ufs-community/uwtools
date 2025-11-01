"""
WaveWatchIII driver tests.
"""

from pathlib import Path

import yaml
from pytest import fixture

from uwtools.drivers.ww3 import WaveWatchIII

# Fixtures


@fixture
def config(tmp_path):
    return {
        "ww3": {
            "namelist": {
                "template_file": str(tmp_path / "ww3_shel.nml.IN"),
                "template_values": {
                    "input_forcing_winds": "C",
                },
            },
            "rundir": str(tmp_path / "run"),
        },
    }


@fixture
def cycle(utc):
    return utc(2024, 2, 1, 18)


@fixture
def driverobj(config, cycle):
    return WaveWatchIII(config=config, cycle=cycle)


# Tests


def test_WaveWatchIII_driver_name(driverobj):
    assert driverobj.driver_name() == WaveWatchIII.driver_name() == "ww3"


def test_WaveWatchIII_namelist_file(driverobj):
    src = driverobj.config["namelist"]["template_file"]
    Path(src).write_text(yaml.dump({}))
    dst = driverobj.rundir / "ww3_shel.nml"
    assert not dst.is_file()
    driverobj.namelist_file()
    assert dst.is_file()


def test_WaveWatchIII_restart_directory(driverobj):
    path = driverobj.rundir / "restart_wave"
    assert not path.is_dir()
    driverobj.restart_directory()
    assert path.is_dir()
