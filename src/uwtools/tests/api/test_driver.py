# pylint: disable=missing-function-docstring,protected-access

from inspect import isclass, ismodule

from pytest import mark

from uwtools.api import driver as driver_api
from uwtools.drivers import driver as driver_lib


@mark.parametrize("classname", ["Assets"])
def test_driver(classname):
    assert getattr(driver_api, classname) is getattr(driver_lib, classname)


def test_no_extras():
    for x in dir(driver_api):
        if not x.startswith("_"):
            obj = getattr(driver_api, x)
            if not ismodule(obj):
                assert isclass(obj)
                assert x in driver_api._CLASSNAMES
