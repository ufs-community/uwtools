# pylint: disable=missing-function-docstring, protected-access
"""
Tests for uwtools.rocoto module.
"""
from importlib import resources

import yaml
from lxml import etree

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


def test_write_rocoto_xml(tmp_path):
    input_yaml = support.fixture_path("hello_workflow.yaml")
    with resources.as_file(resources.files("uwtools.resources")) as resc:
        input_template = resc / "rocoto.jinja2"
    output = tmp_path / "rendered.xml"
    rocoto.write_rocoto_xml(
        input_yaml=input_yaml, input_template=str(input_template), rendered_output=str(output)
    )

    expected = support.fixture_path("hello_workflow.xml")
    support.compare_files(expected, output)


def test_rocoto_xml_is_valid():
    with resources.as_file(resources.files("uwtools.resources")) as resc:
        with open(resc / "schema_with_metatasks.rng", "r", encoding="utf-8") as f:
            schema = etree.RelaxNG(etree.parse(f))

    valid_xml = support.fixture_path("hello_workflow.xml")
    tree = etree.parse(valid_xml)
    assert schema.validate(tree)

    invalid_xml = support.fixture_path("rocoto_invalid.xml")
    tree = etree.parse(invalid_xml)
    assert not schema.validate(tree)
