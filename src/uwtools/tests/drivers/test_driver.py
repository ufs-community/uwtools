# pylint: disable=missing-function-docstring,redefined-outer-name
"""
Tests for uwtools.drivers.driver module.
"""

from importlib import resources
from types import SimpleNamespace as ns
from unittest.mock import patch

import pytest
from pytest import fixture

from uwtools.drivers import driver
from uwtools.drivers.driver import Driver


@fixture
def create_schema(tmp_path):
    schema_file = tmp_path / "schema_file.jsonschema"
    with open(schema_file, "w", encoding="utf-8") as f:
        print(
            """
{
"title": "workflow config",
"description": "This document is to validate config files from SRW, HAFS, Global",
"type": "object",
"properties": {
    "platform": {
        "description": "attributes of the platform",
        "type": "object",
        "properties": {
            "WORKFLOW_MANAGER": {
                "type": "string",
                "enum": ["rocoto", "none"]
                },
            }
        }
    }        
}
""",
            file=f,
        )
    return schema_file


@pytest.mark.usefixtures("create_schema")
class TestDriver(Driver):
    """
    Test concrete class instantiation.
    """

    @property
    def schema(self) -> str:
        return create_schema

    def requirements(self):
        pass

    def resources(self):
        pass

    def output(self):
        pass

    def job_card(self):
        pass


@fixture
def create_config(tmp_path):
    config_file_good = tmp_path / "config_file_good.yaml"
    config_file_bad = tmp_path / "config_file_bad.yaml"

    with open(config_file_good, "w", encoding="utf-8") as f:
        print(
            """
platform:
  WORKFLOW_MANAGER: rocoto
""",
            file=f,
        )
    with open(config_file_bad, "w", encoding="utf-8") as f:
        print(
            """
platform:
  WORKFLOW_MANAGER: 20
""",
            file=f,
        )

    return str(config_file_good), str(config_file_bad)


@pytest.mark.parametrize("valid", [True, False])
def test_validation(valid, create_config):
    # test concrete classes will validate correctly
    config_file_good, config_file_bad = create_config  # pylint: disable=possibly-unused-variable

    instance = TestDriver(config_file=config_file_good if valid else config_file_bad)

    assert instance.validate() is valid
