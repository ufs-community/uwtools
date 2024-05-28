# pylint: disable=missing-function-docstring,protected-access,redefined-outer-name
"""
WW3 driver tests.
"""
from unittest.mock import DEFAULT as D
from unittest.mock import patch

import f90nml  # type: ignore
import yaml
from pytest import fixture, raises

from uwtools.drivers import ww3
from uwtools.exceptions import UWConfigError

# Fixtures


@fixture
def config(tmp_path):
    return {
        "ww3": {
            "namelist": {
                "base_file": str(tmp_path / "namelists.nml"),
                "additional_files": str(tmp_path / "ww3_grid.nml"),
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
    return ww3.WaveWatchIII(config=config_file, batch=True)


# Tests


def test_WaveWatchIII(driverobj):
    assert isinstance(driverobj, ww3.WaveWatchIII)


def test_WaveWatchIII_namelist_file(driverobj):
    dst = driverobj._rundir / "namelists.nml"
    assert not dst.is_file()
    driverobj.namelist_file()
    assert dst.is_file()
    assert isinstance(f90nml.read(dst), f90nml.Namelist)


def test_WaveWatchIII_namelist_missing(driverobj):
    path = driverobj._rundir / "namelists.nml"
    del driverobj._driver_config["namelist"]
    with raises(UWConfigError) as e:
        assert driverobj.namelist_file()
    assert str(e.value) == ("Provide either a 'namelist' YAML block or the %s file" % path)


def test_WaveWatchIII_provisioned_run_directory(driverobj):
    with patch.multiple(
        driverobj,
        namelist_file=D,
    ) as mocks:
        driverobj.provisioned_run_directory()
    for m in mocks:
        mocks[m].assert_called_once_with()


def test_WaveWatchIII__driver_config(driverobj):
    assert driverobj._driver_config == driverobj._config["ww3"]


def test_WaveWatchIII___restart_path(driverobj):
    assert driverobj._restart_path == driverobj._rundir / "restart_wave"


def test_WaveWatchIII__validate(driverobj):
    driverobj._validate()
