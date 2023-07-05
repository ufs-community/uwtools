"""
Tests for uwtools.config_validator module
"""

import pytest

from uwtools import config_validator
from uwtools.logger import Logger
from uwtools.tests.support import fixture_path


@pytest.mark.parametrize("vals", [("good", True), ("bad", False)])
def test_confid_is_valid_good(vals):
    """
    Test that a valid config file succeeds validation.
    """
    cfgtype, boolval = vals
    assert (
        config_validator.config_is_valid(
            config_file=fixture_path(f"schema_test_{cfgtype}.yaml"),
            validation_schema=fixture_path("schema/workflow.jsonschema"),
            log=Logger(),
        )
        is boolval
    )
