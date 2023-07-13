# pylint: disable=missing-function-docstring
"""
Tests for uwtools.config_validator module.
"""

from uwtools import exceptions


def test_UWConfigError():
    exc = exceptions.UWConfigError()
    assert isinstance(exc, Exception)
