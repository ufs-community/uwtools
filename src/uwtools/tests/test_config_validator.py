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
def config_file(tmp_path) -> Path:
    data = {
        "color": "blue",
        "dir": str(tmp_path),
        "number": 88,
        "sub": {
            "dir": str(tmp_path),
        },
    }
    return write_as_json(data, tmp_path / "config.yaml")


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


def test_config_is_valid_good(config_file, schema_file):
    assert config_validator.config_is_valid(
        config_file=config_file,
        schema_file=schema_file,
        log=Logger(),
    )


# @pytest.mark.parametrize("vals", [("good", True), ("bad", False)])
# def test_config_is_valid_good(vals):
#     """
#     Test that good and bad configs pass and fail validation, respectively.
#     """
#     cfgtype, boolval = vals
#     with resources.as_file(resources.files("uwtools.resources")) as path:
#         schema = (path / "workflow.jsonschema").as_posix()
#     assert (
#         config_validator.config_is_valid(
#             config_file=fixture_path(f"schema_test_{cfgtype}.yaml"),
#             validation_schema=schema,
#             log=Logger(),
#         )
#         is boolval
#     )
