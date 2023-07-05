# pylint: disable=missing-function-docstring,redefined-outer-name
"""
Tests for uwtools.config_validator module
"""
import json

import jsonschema
import pytest
import yaml
from pytest import fixture, raises

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


def validate(subpath, schema):
    with open(fixture_path(subpath), "r", encoding="utf-8") as f:
        jsonschema.validate(yaml.safe_load(f), schema)


@fixture(scope="module")
def schema():
    with open(fixture_path("schema/salad.jsonschema"), "r", encoding="utf-8") as f:
        return json.load(f)


def test_validate_bad_yaml(schema):
    with raises(jsonschema.exceptions.ValidationError):
        validate("bad_fruit_config.yaml", schema)


def test_validate_good_yaml(schema, capsys):
    validate("fruit_config_similar.yaml", schema)
    assert capsys.readouterr().err == ""
    assert capsys.readouterr().out == ""
