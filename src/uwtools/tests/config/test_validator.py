# pylint: disable=missing-function-docstring,protected-access,redefined-outer-name
"""
Tests for uwtools.config.validator module.
"""
import json
import logging
from importlib import resources
from pathlib import Path
from typing import Any, Dict
from unittest.mock import Mock, patch

import pytest
from pytest import fixture

from uwtools.config import validator
from uwtools.tests.support import fixture_path, logged

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


@pytest.mark.parametrize(
    "vals", [("hello_workflow_tags.yaml", True), ("hello_workflow_invalid.yaml", False)]
)
def test_validate_workflow_tags_pass(vals):
    fn, validity = vals
    with resources.as_file(resources.files("uwtools.resources")) as resc:
        schema_file = resc / "rocoto.jsonschema"
    config_file = fixture_path(fn)
    assert (
        validator.validate_yaml(schema_file=schema_file, config_file=config_file, check_path=False)
        is validity
    )


@fixture
def rocoto_assets():
    with resources.as_file(resources.files("uwtools.resources")) as resc:
        schema_file = resc / "rocoto.jsonschema"
    return schema_file, {
        "workflow": {
            "cycledefs": {"howdy": ["202209290000 202209300000 06:00:00"]},
            "log": "/some/path/to/&FOO;",
            "tasks": {
                "metatask": {
                    "var": {"member": "foo bar baz"},
                    "task": {
                        "cores": 88,
                        "command": "some-command",
                        "walltime": "00:01:00",
                    },
                },
            },
        },
    }


def test_validate_yaml_rocoto_invalid_no_command(rocoto_assets, caplog):
    schema_file, config_dict = rocoto_assets
    del config_dict["workflow"]["tasks"]["metatask"]["task"]["command"]
    with patch.object(validator, "YAMLConfig") as YAMLConfig:
        yaml_config = YAMLConfig()
        yaml_config.data = config_dict
        assert (
            validator.validate_yaml(
                schema_file=schema_file, config_file="/not/used", check_path=False
            )
            is False
        )
        assert logged(caplog, "'command' is a required property")


def test_validate_yaml_rocoto_invalid_no_task(rocoto_assets, caplog):
    schema_file, config_dict = rocoto_assets
    del config_dict["workflow"]["tasks"]["metatask"]["task"]
    with patch.object(validator, "YAMLConfig") as YAMLConfig:
        yaml_config = YAMLConfig()
        yaml_config.data = config_dict
        assert (
            validator.validate_yaml(
                schema_file=schema_file, config_file="/not/used", check_path=False
            )
            is False
        )
        assert logged(caplog, "{'var': {'member': 'foo bar baz'}} does not have enough properties")


def test_validate_yaml_rocoto_invalid_no_var(rocoto_assets, caplog):
    schema_file, config_dict = rocoto_assets
    del config_dict["workflow"]["tasks"]["metatask"]["var"]
    with patch.object(validator, "YAMLConfig") as YAMLConfig:
        yaml_config = YAMLConfig()
        yaml_config.data = config_dict
        assert (
            validator.validate_yaml(
                schema_file=schema_file, config_file="/not/used", check_path=False
            )
            is False
        )
        assert logged(caplog, "'var' is a required property")


def test_validate_yaml_rocoto_invalid_type(rocoto_assets, caplog):
    schema_file, config_dict = rocoto_assets
    config_dict["workflow"]["tasks"]["metatask"]["task"]["cores"] = "string"
    with patch.object(validator, "YAMLConfig") as YAMLConfig:
        yaml_config = YAMLConfig()
        yaml_config.data = config_dict
        assert (
            validator.validate_yaml(
                schema_file=schema_file, config_file="/not/used", check_path=False
            )
            is False
        )
        assert logged(caplog, "'string' is not of type 'integer'")


def test_validate_yaml_rocoto_invalid_walltime_pattern(rocoto_assets, caplog):
    schema_file, config_dict = rocoto_assets
    config_dict["workflow"]["tasks"]["metatask"]["task"]["walltime"] = "0:01:00"
    with patch.object(validator, "YAMLConfig") as YAMLConfig:
        yaml_config = YAMLConfig()
        yaml_config.data = config_dict
        assert (
            validator.validate_yaml(
                schema_file=schema_file, config_file="/not/used", check_path=False
            )
            is False
        )
        assert logged(caplog, "'0:01:00' does not match '^[0-9]{2}:[0-9]{2}:[0-9]{2}$'")


def test_validate_yaml_rocoto_valid(rocoto_assets, caplog):
    schema_file, config_dict = rocoto_assets
    with patch.object(validator, "YAMLConfig") as YAMLConfig:
        yaml_config = YAMLConfig()
        yaml_config.data = config_dict
        assert (
            validator.validate_yaml(
                schema_file=schema_file, config_file="/not/used", check_path=False
            )
            is True
        )


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
