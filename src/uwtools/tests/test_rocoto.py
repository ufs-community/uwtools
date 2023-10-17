# pylint: disable=missing-function-docstring, protected-access
"""
Tests for uwtools.rocoto module.
"""

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


def test__add_tasks():
    with resources.as_file(resources.files("uwtools.tests.fixtures")) as path:
        input_yaml = (path / "hello_workflow.yaml").as_posix()

    values = YAMLConfig(input_yaml)
    tasks = values["workflow"]["tasks"]
    with patch.object(rocoto, "_add_jobname") as module:
        rocoto._add_tasks(input_yaml)
    assert module.called_once_with(tasks)


def test__rocoto_template():
    with resources.as_file(resources.files("uwtools.resources")) as path:
        expected = (path / "schema_with_metatasks.rng").as_posix()
    assert rocoto._rocoto_template() == expected


def test__rocoto_schema():
    with resources.as_file(resources.files("uwtools.resources")) as path:
        expected = (path / "rocoto.jsonschema").as_posix()
    assert rocoto._rocoto_schema() == expected


@pytest.mark.parametrize("vals", [("hello_workflow.yaml", True), ("fruit_config.yaml", False)])
def test_realize_rocoto_xml(vals, tmp_path):
    fn, validity = vals
    output = tmp_path / "rendered.xml"

    with patch.object(rocoto, "validate_rocoto_xml", value=True):
        with patch.object(rocoto.uwtools.config.validator, "_bad_paths", return_value=None):
            with resources.as_file(resources.files("uwtools.tests.fixtures")) as path:
                input_yaml = (path / fn).as_posix()
                result = rocoto.realize_rocoto_xml(input_yaml=input_yaml, rendered_output=output)
    assert result is validity


def test_realize_rocoto_invalid_xml():
    input_yaml = support.fixture_path("hello_workflow.yaml")
    output = support.fixture_path("rocoto_invalid.xml")
    with patch.object(rocoto, "write_rocoto_xml", return_value=None):
        result = rocoto.realize_rocoto_xml(input_yaml=input_yaml, rendered_output=output)
    assert result is False


@pytest.mark.parametrize("vals", [("hello_workflow.xml", True), ("rocoto_invalid.xml", False)])
def test_rocoto_xml_is_valid(vals):
    fn, validity = vals
    xml = support.fixture_path(fn)
    result = rocoto.validate_rocoto_xml(input_xml=xml)

    assert result is validity


def test__write_rocoto_xml(tmp_path):
    input_yaml = support.fixture_path("hello_workflow.yaml")
    output = tmp_path / "rendered.xml"

    with patch.object(rocoto, "_add_tasks", return_value=None):
        rocoto._write_rocoto_xml(input_yaml=input_yaml, rendered_output=output)

    expected = support.fixture_path("hello_workflow.xml")
    support.compare_files(expected, output)
