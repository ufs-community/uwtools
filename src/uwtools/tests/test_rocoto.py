# pylint: disable=missing-function-docstring, protected-access
"""
Tests for uwtools.rocoto module.
"""

from importlib import resources

import pytest
import yaml

from uwtools import rocoto
from uwtools.tests import support

# Test functions


def test_add_jobname():
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


def test__rocoto_template():
    with resources.as_file(resources.files("uwtools.resources")) as path:
        expected = (path / "rocoto.jinja2").as_posix()
    assert rocoto._rocoto_template() == expected


def test__rocoto_schema():
    with resources.as_file(resources.files("uwtools.resources")) as path:
        expected = (path / "rocoto.jsonschema").as_posix()
    assert rocoto._rocoto_schema() == expected


def test_write_rocoto_xml(tmp_path):
    input_yaml = support.fixture_path("hello_workflow.yaml")
    with resources.as_file(resources.files("uwtools.resources")) as resc:
        input_template = resc / "rocoto.jinja2"
    output = tmp_path / "rendered.xml"
    rocoto.write_rocoto_xml(
        input_yaml=input_yaml, input_template=input_template, rendered_output=output
    )

    expected = support.fixture_path("hello_workflow.xml")
    support.compare_files(expected, output)


@pytest.mark.parametrize("vals", [("hello_workflow.xml", True), ("rocoto_invalid.xml", False)])
def test_rocoto_xml_is_valid(vals):
    fn, validity = vals
    with resources.as_file(resources.files("uwtools.resources")) as resc:
        xml = support.fixture_path(fn)
        schema = resc / "schema_with_metatasks.rng"
    result = rocoto.validate_rocoto_xml(input_xml=xml, schema_file=schema)

    assert result is validity
