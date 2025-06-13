"""
API access to the ``uwtools`` driver base classes.
"""

from importlib import import_module
from inspect import getmembers, isclass
from pkgutil import iter_modules

from uwtools.drivers.driver import (
    Assets,
    AssetsCycleBased,
    AssetsCycleLeadtimeBased,
    AssetsTimeInvariant,
    Driver,
    DriverCycleBased,
    DriverCycleLeadtimeBased,
    DriverTimeInvariant,
)


def yaml_keys_to_classes() -> dict[str, type]:
    """
    Returns a mapping from UW YAML driver-block keys to their associated driver classes.
    """
    pkgname = "uwtools.api"
    mapping = {}
    for modinfo in iter_modules(import_module(pkgname).__path__):
        module = import_module(f"{pkgname}.{modinfo.name}")
        for driver_class in {obj for _, obj in getmembers(module) if isclass(obj)}:
            try:
                yaml_key = driver_class.driver_name()
            except AttributeError:  # noqa: PERF203
                pass
            else:
                if yaml_key:
                    mapping[yaml_key] = driver_class
    return mapping


__all__ = [
    "Assets",
    "AssetsCycleBased",
    "AssetsCycleLeadtimeBased",
    "AssetsTimeInvariant",
    "Driver",
    "DriverCycleBased",
    "DriverCycleLeadtimeBased",
    "DriverTimeInvariant",
    "yaml_keys_to_classes",
]
