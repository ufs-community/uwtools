# pylint: disable=missing-function-docstring
"""
Tests for uwtools.drivers.driver module.
"""

from importlib import resources
from unittest.mock import patch

import pytest

from uwtools.drivers import driver


def test_import():
    # Test stub asserting that module was imported.
    assert dir(driver)


@patch.multiple("driver.Driver.__abstractmethods__", set())
def test_instance():
    # test instantiation of abstract class
    instance = driver.Driver()
    assert instance is not None
