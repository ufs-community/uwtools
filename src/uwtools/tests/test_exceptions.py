"""
Tests for uwtools.config_validator module.
"""

from uwtools import exceptions


def test_parent_UWError():
    exc = exceptions.UWError()
    assert isinstance(exc, Exception)


def test_UWConfigError():
    exc = exceptions.UWConfigError()
    assert isinstance(exc, Exception)
