# pylint: disable=duplicate-code,missing-function-docstring,redefined-outer-name
"""
sfc_climo_gen driver tests.
"""
# import datetime as dt
# from functools import partial
from pathlib import Path

# import pytest
# import yaml
from pytest import fixture

from uwtools.drivers import sfc_climo_gen

# from unittest.mock import DEFAULT as D
# from unittest.mock import PropertyMock, patch


# from uwtools.tests.support import logged, validator, with_del, with_set


@fixture
def config_file():
    return Path("/home/Paul.Madden/git/uwtools/config.yaml")


@fixture
def driverobj(config_file):
    return sfc_climo_gen.SfcClimoGen(config_file=config_file, batch=True)


# Driver tests


def test_SfcClimoGen(driverobj):
    assert isinstance(driverobj, sfc_climo_gen.SfcClimoGen)
