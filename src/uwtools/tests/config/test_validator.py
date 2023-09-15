# pylint: disable=missing-function-docstring,protected-access,redefined-outer-name
"""
Tests for uwtools.config.validator module.
"""

import json
import logging
from importlib import resources
from pathlib import Path
from typing import Any, Dict

from pytest import fixture

from uwtools.config import validator
from uwtools.tests import support

# Support functions


@fixture
def config(tmp_path) -> Dict[str, Any]:
    return {
        "color": "blue",
        "dir": str(tmp_path),
        "number": 88,
        "sub": {
            "dir": str(tmp_path),
        },
    }


@fixture
def config_file(tmp_path) -> str:
    return str(tmp_path / "config.yaml")


@fixture
def schema() -> Dict[str, Any]:
    return {
        "properties": {
            "color": {
                "enum": ["blue", "red"],
                "type": "string",
            },
            "dir": {
                "format": "uri",
                "type": "string",
            },
            "number": {"type": "number"},
            "sub": {
                "properties": {
                    "dir": {
                        "format": "uri",
                        "type": "string",
                    },
                    "type": "object",
                },
            },
        },
        "type": "object",
    }


@fixture
def schema_file(tmp_path) -> str:
    return str(tmp_path / "schema.yaml")


def write_as_json(data: Dict[str, Any], path: Path) -> Path:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return path


# Test functions


def test_validate_yaml_fail_bad_dir_top(caplog, config, config_file, schema, schema_file, tmp_path):
    # Specify a non-existent directory for the topmost directory value.
    logging.getLogger().setLevel(logging.INFO)
    d = str(tmp_path / "no-such-dir")
    config["dir"] = d
    write_as_json(config, config_file)
    write_as_json(schema, schema_file)
    assert not validator.validate_yaml(schema_file=schema_file, config_file=config_file)
    assert len([x for x in caplog.records if f"Path does not exist: {d}" in x.message]) == 1


def test_validate_yaml_fail_bad_dir_nested(
    caplog, config, config_file, schema, schema_file, tmp_path
):
    # Specify a non-existent directory for the nested directory value.
    logging.getLogger().setLevel(logging.INFO)
    d = str(tmp_path / "no-such-dir")
    config["sub"]["dir"] = d
    write_as_json(config, config_file)
    write_as_json(schema, schema_file)
    assert not validator.validate_yaml(schema_file=schema_file, config_file=config_file)
    assert len([x for x in caplog.records if f"Path does not exist: {d}" in x.message]) == 1


def test_validate_yaml_fail_bad_enum_val(caplog, config, config_file, schema, schema_file):
    # Specify an invalid enum value.
    logging.getLogger().setLevel(logging.INFO)
    config["color"] = "yellow"
    write_as_json(config, config_file)
    write_as_json(schema, schema_file)
    assert not validator.validate_yaml(schema_file=schema_file, config_file=config_file)
    assert any(x for x in caplog.records if "1 schema-validation error found" in x.message)
    assert any(x for x in caplog.records if "'yellow' is not one of" in x.message)


def test_validate_yaml_fail_bad_number_val(caplog, config, config_file, schema, schema_file):
    # Specify an invalid number value.
    logging.getLogger().setLevel(logging.INFO)
    config["number"] = "string"
    write_as_json(config, config_file)
    write_as_json(schema, schema_file)
    assert not validator.validate_yaml(schema_file=schema_file, config_file=config_file)
    assert any(x for x in caplog.records if "1 schema-validation error found" in x.message)
    assert any(x for x in caplog.records if "'string' is not of type 'number'" in x.message)


def test_validate_yaml_pass(config, config_file, schema, schema_file):
    # Test a fully valid config file.
    write_as_json(config, config_file)
    write_as_json(schema, schema_file)
    assert validator.validate_yaml(schema_file=schema_file, config_file=config_file)


def test_validate_workflow_tags_pass():
    # Test a fully valid config file passes schema
    with resources.as_file(resources.files("uwtools.resources")) as resc:
        schema_file = resc / "rocoto.jsonschema"
    config_file = support.fixture_path("hello_workflow_tags.yaml")
    assert validator.validate_yaml(schema_file=schema_file, config_file=config_file, check_path=False)


def test__bad_paths_top(config, schema, tmp_path):
    d = str(tmp_path / "no-such-dir")
    config["dir"] = d
    assert validator._bad_paths(config, schema) == [d]


def test__bad_paths_nested(config, schema, tmp_path):
    d = str(tmp_path / "no-such-dir")
    config["sub"]["dir"] = d
    assert validator._bad_paths(config, schema) == [d]


def test__bad_paths_none(config, schema):
    assert not validator._bad_paths(config, schema)


def test__validation_errors_bad_enum_value(config, schema):
    config["color"] = "yellow"
    assert len(validator._validation_errors(config, schema)) == 1


def test__validation_errors_bad_number_value(config, schema):
    config["number"] = "string"
    assert len(validator._validation_errors(config, schema)) == 1


def test__validation_errors_pass(config, schema):
    assert not validator._validation_errors(config, schema)
