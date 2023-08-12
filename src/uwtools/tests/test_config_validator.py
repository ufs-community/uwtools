# pylint: disable=missing-function-docstring,redefined-outer-name
"""
Tests for uwtools.config_validator module.
"""
import json
from pathlib import Path
from typing import Any, Dict

from pytest import fixture

from uwtools import config_validator
from uwtools.logger import Logger

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
def schema_file(tmp_path) -> Path:
    data = {
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
    return write_as_json(data, tmp_path / "schema.yaml")


def write_as_json(data: Dict[str, Any], path: Path) -> Path:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return path


# Test functions


def test_config_is_valid_fail_bad_dir_top(caplog, config, config_file, schema_file, tmp_path):
    # Specify a non-existent directory for the topmost directory value.
    d = str(tmp_path / "no-such-dir")
    config["dir"] = d
    write_as_json(config, config_file)
    assert not config_validator.config_is_valid(config_file, schema_file, log=Logger())
    assert len([x for x in caplog.records if f"Path does not exist: {d}" in x.message]) == 1


def test_config_is_valid_fail_bad_dir_nested(caplog, config, config_file, schema_file, tmp_path):
    # Specify a non-existent directory for the nested directory value.
    d = str(tmp_path / "no-such-dir")
    config["sub"]["dir"] = d
    write_as_json(config, config_file)
    assert not config_validator.config_is_valid(config_file, schema_file, log=Logger())
    assert len([x for x in caplog.records if f"Path does not exist: {d}" in x.message]) == 1


def test_config_is_valid_fail_bad_enum_val(caplog, config, config_file, schema_file):
    # Specify an invalid enum value.
    config["color"] = "yellow"
    write_as_json(config, config_file)
    assert not config_validator.config_is_valid(config_file, schema_file, log=Logger())
    assert any(x for x in caplog.records if "1 schema-validation error found" in x.message)
    assert any(x for x in caplog.records if "'yellow' is not one of" in x.message)


def test_config_is_valid_fail_bad_number_val(caplog, config, config_file, schema_file):
    # Specify an invalid number value.
    config["number"] = "string"
    write_as_json(config, config_file)
    assert not config_validator.config_is_valid(config_file, schema_file, log=Logger())
    assert any(x for x in caplog.records if "1 schema-validation error found" in x.message)
    assert any(x for x in caplog.records if "'string' is not of type 'number'" in x.message)


def test_config_is_valid_pass(config, config_file, schema_file):
    # Test a fully valid config file.
    write_as_json(config, config_file)
    assert config_validator.config_is_valid(config_file, schema_file, log=Logger())
