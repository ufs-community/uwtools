# pylint: disable=missing-function-docstring
"""
Tests for uwtools.drivers.driver module.
"""

from importlib import resources

import pytest

from uwtools.drivers import driver
from uwtools.tests.support import fixture_path


def test_import():
    # Test stub asserting that module was imported.
    assert dir(driver)


@pytest.mark.parametrize("vals", [("good", True), ("bad", False)])
def test_FV3Forecast_config_is_valid_good(vals):
    """
    Test that a valid config file succeeds validation.
    """
    cfgtype, boolval = vals
    with resources.as_file(resources.files("uwtools.resources")) as path:
        schema = (path / "FV3Forecast.jsonschema").as_posix()
    method = driver.Driver.validate
    assert method(config_file=fixture_path(f"schema_test_{cfgtype}.yaml"), schema=schema) is boolval
