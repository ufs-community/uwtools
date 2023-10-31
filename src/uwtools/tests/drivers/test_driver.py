# pylint: disable=missing-function-docstring,redefined-outer-name
"""
Tests for uwtools.drivers.driver module.
"""

import datetime
import logging
from collections.abc import Mapping
from pathlib import Path
from unittest.mock import patch

import pytest
from pytest import fixture

from uwtools.drivers.driver import Driver
from uwtools.logging import log
from uwtools.tests.support import logged


class ConcreteDriver(Driver):
    """
    Driver subclass for testing purposes.
    """

    def batch_script(self):
        pass

    def output(self):
        pass

    def requirements(self):
        pass

    def resources(self) -> Mapping:
        return {}

    def run(self, cycle: datetime.date) -> bool:
        return True

    def run_cmd(self, *args):
        pass

    @property
    def schema_file(self) -> Path:
        return Path()


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
  "description": "This document is to validate user-defined FV3 forecast config files",
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
def test_validation(caplog, configs, schema, tmp_path, valid):
    config_good, config_bad = configs
    config_file = str(tmp_path / "config.yaml")
    with open(config_file, "w", encoding="utf-8") as f:
        print(config_good if valid else config_bad, file=f)
    schema_file = str(tmp_path / "test.jsonschema")
    with open(schema_file, "w", encoding="utf-8") as f:
        print(schema, file=f)
    with patch.object(ConcreteDriver, "schema_file", new=schema_file):
        log.setLevel(logging.INFO)
        ConcreteDriver(config_file=config_file)
        if valid:
            assert logged(caplog, "0 schema-validation errors found")
        else:
            assert logged(caplog, "2 schema-validation errors found")
