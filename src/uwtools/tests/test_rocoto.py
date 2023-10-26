# pylint: disable=missing-function-docstring, protected-access
"""
Tests for uwtools.rocoto module.
"""

import tempfile
from importlib import resources
from unittest.mock import patch

import pytest
import yaml

from uwtools import rocoto
from uwtools.config.core import YAMLConfig
from uwtools.tests import support

# Test functions


def test__add_jobname():
    expected = yaml.safe_load(
        """
task_hello:
  command: echo hello 
  jobname: hello
metatask_howdy:
  foo: bar
  task_howdy_#mem#:
    command: echo hello 
    jobname: howdy_#mem#
"""
    )

    tree = yaml.safe_load(
        """
task_hello:
  command: echo hello
metatask_howdy:
  foo: bar
  task_howdy_#mem#:
    command: echo hello 
"""
    )

    rocoto._add_jobname(tree)
    assert expected == tree


def test__add_jobname_to_tasks():
    with resources.as_file(resources.files("uwtools.tests.fixtures")) as path:
        input_yaml = path / "hello_workflow.yaml"

    values = YAMLConfig(input_yaml)
    tasks = values["workflow"]["tasks"]
    with patch.object(rocoto, "_add_jobname") as module:
        rocoto._add_jobname_to_tasks(input_yaml)
    assert module.called_once_with(tasks)


def test__rocoto_schema_yaml():
    with resources.as_file(resources.files("uwtools.resources")) as path:
        expected = path / "rocoto.jsonschema"
    assert rocoto._rocoto_schema_yaml() == expected


def test__rocoto_schema_xml():
    with resources.as_file(resources.files("uwtools.resources")) as path:
        expected = path / "schema_with_metatasks.rng"
    assert rocoto._rocoto_schema_xml() == expected


@pytest.mark.parametrize("vals", [("hello_workflow.yaml", True), ("fruit_config.yaml", False)])
def test_realize_rocoto_xml(vals, tmp_path):
    fn, validity = vals
    output = tmp_path / "rendered.xml"

    with patch.object(rocoto, "validate_rocoto_xml", value=True):
        with resources.as_file(resources.files("uwtools.tests.fixtures")) as path:
            config_file = path / fn
            result = rocoto.realize_rocoto_xml(config_file=config_file, rendered_output=output)
    assert result is validity


def test_realize_rocoto_default_output():
    with patch.object(rocoto, "validate_rocoto_xml", value=True):
        with resources.as_file(resources.files("uwtools.tests.fixtures")) as path:
            config_file = path / "hello_workflow.yaml"
            result = rocoto.realize_rocoto_xml(config_file=config_file)
    assert result is True


def test_realize_rocoto_invalid_xml():
    config_file = support.fixture_path("hello_workflow.yaml")
    xml = support.fixture_path("rocoto_invalid.xml")
    with patch.object(rocoto, "_write_rocoto_xml", return_value=None):
        with patch.object(tempfile, "NamedTemporaryFile") as temp:
            temp.return_value.name = xml
            result = rocoto.realize_rocoto_xml(config_file=config_file, rendered_output=xml)
    assert result is False


@pytest.mark.parametrize("vals", [("hello_workflow.xml", True), ("rocoto_invalid.xml", False)])
def test_rocoto_xml_is_valid(vals):
    fn, validity = vals
    xml = support.fixture_path(fn)
    result = rocoto.validate_rocoto_xml(input_xml=xml)

    assert result is validity


def test__write_rocoto_xml(tmp_path):
    config_file = support.fixture_path("hello_workflow.yaml")
    output = tmp_path / "rendered.xml"

    rocoto._write_rocoto_xml(config_file=config_file, rendered_output=output)

    expected = support.fixture_path("hello_workflow.xml")
    assert support.compare_files(expected, output) is True
