# pylint: disable=missing-function-docstring
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
        print("undefined_filter: '{{ 34 | not_a_filter }}'", file=f)
    return schema_file


@pytest.mark.usefixtures("create_schema")
class Testinstance(Driver):
    """
    Test concrete class instantiation.
    """

    @property
    def schema(self) -> str:
        return create_schema

    def requirements(self):
        """
        requirements.
        """

    def resources(self):
        """
        resources.
        """

    def output(self):
        """
        output.
        """

    def job_card(self):
        """
        job_card.
        """


@fixture
def create_config(tmp_path):
    config_file_good = tmp_path / "config_file_good.yaml"
    config_file_bad = tmp_path / "config_file_bad.yaml"

    with open(config_file_good, "w", encoding="utf-8") as f:
        print("undefined_filter: '{{ 34 | not_a_filter }}'", file=f)
    with open(config_file_bad, "w", encoding="utf-8") as f:
        print("undefined_filter: '{{ 34 | not_a_filter }}'", file=f)

    return str(config_file_good), str(config_file_bad)


@pytest.mark.parametrize("vals", [("good", True), ("bad", False)])
def test_validation(vals, create_config):
    # test concrete classes will validate correctly
    config_file_good, config_file_bad = create_config  # pylint: disable=unused-variable
    cfgtype, boolval = vals

    instance = Testinstance(config_file=f"config_file_{cfgtype}.yaml")

    assert instance.validate() is boolval
