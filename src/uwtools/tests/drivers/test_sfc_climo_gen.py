# pylint: disable=missing-function-docstring,redefined-outer-name
"""
sfc_climo_gen driver tests.
"""
from pathlib import Path

from pytest import fixture

from uwtools.drivers import sfc_climo_gen


@fixture
def config_file():
    return Path("/home/Paul.Madden/git/uwtools/config-scg.yaml")


@fixture
def driverobj(config_file):
    return sfc_climo_gen.SfcClimoGen(config_file=config_file, batch=True)


# Driver tests


def test_SfcClimoGen(driverobj):
    assert isinstance(driverobj, sfc_climo_gen.SfcClimoGen)
