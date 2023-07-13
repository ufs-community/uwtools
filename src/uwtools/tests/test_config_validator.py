# pylint: disable=missing-function-docstring,redefined-outer-name
"""
Tests for uwtools.config_validator module.
"""

from importlib import resources

import pytest

from uwtools import config_validator
from uwtools.logger import Logger
from uwtools.tests.support import fixture_path


@pytest.mark.parametrize("vals", [("good", True), ("bad", False)])
def test_config_is_valid_good(vals):
    """
    Test that a valid config file succeeds validation.
    """
    cfgtype, boolval = vals
    with resources.as_file(resources.files("uwtools.resources")) as path:
        schema = (path / "workflow.jsonschema").as_posix()
    assert (
        config_validator.config_is_valid(
            config_file=fixture_path(f"schema_test_{cfgtype}.yaml"),
            validation_schema=schema,
            log=Logger(),
        )
        is boolval
    )
