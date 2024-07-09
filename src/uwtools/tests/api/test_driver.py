# pylint: disable=missing-function-docstring,protected-access

from inspect import isclass, ismodule

from pytest import mark

from uwtools.api import driver as driver_api
from uwtools.drivers import driver as driver_lib


@mark.parametrize("classname", driver_api._CLASSNAMES)
def test_driver(classname):
    assert getattr(driver_api, classname) is getattr(driver_lib, classname)


def test_public_attributes():
    # Check that the module is not accidentally exposing unexpected public atttributes. Ignore
    # private attributes and imported modules and assert that what remains is an intentionally
    # exposed (driver) class.
    for name in dir(driver_api):
        obj = getattr(driver_api, name)
        if name.startswith("_") or ismodule(obj):
            continue
        assert isclass(obj)
        assert name in driver_api._CLASSNAMES
