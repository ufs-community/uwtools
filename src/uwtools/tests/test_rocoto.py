# pylint: disable=missing-function-docstring
"""
Tests for uwtools.rocoto module.
"""
from importlib import resources

import yaml

from uwtools import rocoto
from uwtools.tests import support

# pylint: disable=protected-access

# Test functions


def test_add_jobname():
    expected = yaml.safe_load(
        """
task_hello:
  command: echo hello 
  jobname: hello
metatask_howdy:
  task_howdy_#mem#:
    command: echo hello 
    jobname: howdy_#mem#
"""
    )

    tasks = yaml.safe_load(
        """
task_hello:
  command: echo hello
metatask_howdy:
  task_howdy_#mem#:
    command: echo hello 
"""
    )

    rocoto._add_jobname(tasks)
    assert expected == tasks


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
