# pylint: disable=missing-function-docstring
"""
Tests for uwtools.drivers.driver module.
"""

from importlib import resources
from unittest.mock import patch

import pytest

from uwtools.drivers import driver
from uwtools.drivers.driver import Driver
from uwtools.tests.support import fixture_path


def test_import():
    # Test stub asserting that module was imported.
    assert dir(driver)


@pytest.mark.parametrize("cls", Driver.__subclasses__())
@pytest.mark.parametrize("vals", [("good", True), ("bad", False)])
def test_instance(cls, vals):
    # test instantiation of abstract class
    patch.multiple(cls, __abstractmethods__=set())

    cfgtype, boolval = vals
    instance = cls(config_file=fixture_path(f"schema_test_{cfgtype}.yaml"))

    assert instance is not None

    # test concrete classes will validate correctly
    assert instance.validate() is boolval
