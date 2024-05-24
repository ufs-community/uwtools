# pylint: disable=missing-function-docstring,protected-access,redefined-outer-name
"""
WW3 driver tests.
"""
from unittest.mock import DEFAULT as D
from unittest.mock import patch

import f90nml  # type: ignore
import yaml
from pytest import fixture

from uwtools.drivers import ww3

# Fixtures


@fixture
def config(tmp_path):
    return {
        "ww3": {
            "namelist": {
                "base_file": str(tmp_path / "namelists.nml"),
                "additional_files": str(tmp_path / "additional.nml"),
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
    with open(driverobj._driver_config["namelist"]["base_file"], "w", encoding="utf-8") as f:
        print(
            "&MISC CICE0 = 0.25, CICEN = 0.75, FLAGTR = 4 / "
            "&FLX3 CDMAX = 3.5E-3 , CTYPE = 0 / END OF NAMELISTS",
            file=f,
        )
    dst = driverobj._rundir / "namelists.nml"
    driverobj.namelist_file()
    assert dst.is_file()
    nml = f90nml.read(dst)
    assert isinstance(nml, f90nml.Namelist)
    assert nml["MISC"]["CICE0"] == 0.25
    assert nml["MISC"]["CICEN"] == 0.75
    assert nml["MISC"]["FLAGTR"] == 4
    assert nml["FLX3"]["CDMAX"] == 3.5e-3
    assert nml["FLX3"]["CTYPE"] == 0


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


def test_WaveWatchIII__validate(driverobj):
    driverobj._validate()
