# pylint: disable=missing-function-docstring

from pytest import mark

from uwtools.api import driver as driver_api
from uwtools.drivers import driver as driver_lib


@mark.parametrize(
    "classname",
    [
        "Assets",
        "AssetsCycleBased",
        "AssetsCycleLeadtimeBased",
        "AssetsTimeInvariant",
        "Driver",
        "DriverCycleBased",
        "DriverCycleLeadtimeBased",
        "DriverTimeInvariant",
    ],
)
def test_driver(classname):
    assert getattr(driver_api, classname) is getattr(driver_lib, classname)
