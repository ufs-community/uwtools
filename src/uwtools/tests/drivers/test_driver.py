# pylint: disable=missing-function-docstring,redefined-outer-name
"""
Tests for uwtools.drivers.driver module.
"""

from unittest.mock import patch

import pytest
from pytest import fixture

from uwtools.drivers.driver import Driver


class ConcreteDriver(Driver):
    """
    Driver subclass for testing purposes.
    """

    @property
    def schema(self) -> str:
        return ""

    def requirements(self):
        pass

    def resources(self):
        pass

    def output(self):
        pass

    def job_card(self):
        pass


@fixture
def configs():
    config_good = """
platform:
  WORKFLOW_MANAGER: rocoto
"""
    config_bad = """
platform:
  WORKFLOW_MANAGER: 20
"""
    return config_good, config_bad


@fixture
def schema():
    return """
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
          "enum": [
            "rocoto",
            "none"
          ]
        }
      }
    }
  }
}
""".strip()


@pytest.mark.parametrize("valid", [True, False])
def test_validation(configs, schema, tmp_path, valid):
    config_good, config_bad = configs
    config_file = str(tmp_path / "config.yaml")
    with open(config_file, "w", encoding="utf-8") as f:
        print(config_good if valid else config_bad, file=f)
    schema_file = str(tmp_path / "test.jsonschema")
    with open(schema_file, "w", encoding="utf-8") as f:
        print(schema, file=f)
    with patch.object(ConcreteDriver, "schema", new=schema_file):
        instance = ConcreteDriver(config_file=config_file)
        assert instance.validate() is valid
