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
def test_api_driver(classname):
    assert getattr(driver_api, classname) is getattr(driver_lib, classname)


def test_api_driver_yaml_keys_to_classes():
    mapping = driver_api.yaml_keys_to_classes()
    assert mapping
    for k, v in mapping.items():
        assert isinstance(k, str)
        assert issubclass(v, driver_api.Assets)
