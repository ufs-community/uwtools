# pylint: disable=missing-function-docstring,redefined-outer-name

"""
Tests for schema validation tool
"""

import json

import jsonschema
import yaml
from pytest import fixture, raises

from uwtools.test.support import fixture_path


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
