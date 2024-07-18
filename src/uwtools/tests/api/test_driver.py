# pylint: disable=missing-function-docstring,protected-access

from pytest import mark

from uwtools.api import driver as driver_api
from uwtools.drivers import driver as driver_lib


@mark.parametrize("classname", driver_api._CLASSNAMES)
def test_driver(classname):
    assert getattr(driver_api, classname) is getattr(driver_lib, classname)
