# pylint: disable=missing-function-docstring, protected-access
"""
Tests for uwtools.rocoto module.
"""

import shutil
from unittest.mock import patch

import pytest
import yaml

from uwtools import rocoto
from uwtools.config.core import YAMLConfig
from uwtools.tests.support import compare_files, fixture_path, resource_pathobj

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
    cfgfile = fixture_path("hello_workflow.yaml")
    values = YAMLConfig(cfgfile)
    tasks = values["workflow"]["tasks"]
    with patch.object(rocoto, "_add_jobname") as module:
        rocoto._add_jobname_to_tasks(cfgfile)
    assert module.called_once_with(tasks)


def test__rocoto_schema_yaml():
    assert rocoto._rocoto_schema_yaml() == resource_pathobj("rocoto.jsonschema")


def test__rocoto_schema_xml():
    assert rocoto._rocoto_schema_xml() == resource_pathobj("schema_with_metatasks.rng")


def test_realize_rocoto_default_output():
    cfgfile = fixture_path("hello_workflow.yaml")
    with patch.object(rocoto, "validate_rocoto_xml", value=True):
        assert rocoto.realize_rocoto_xml(config_file=cfgfile) is True


def test_realize_rocoto_invalid_xml(tmp_path):
    cfgfile = fixture_path("hello_workflow.yaml")
    outfile = tmp_path / "rocoto.xml"
    dump = lambda _, dst: shutil.copyfile(fixture_path("rocoto_invalid.xml"), dst)
    with patch.object(rocoto.RocotoXML, "dump", dump):
        success = rocoto.realize_rocoto_xml(config_file=cfgfile, output_file=outfile)
    assert success is False


@pytest.mark.parametrize("vals", [("hello_workflow.xml", True), ("rocoto_invalid.xml", False)])
def test_rocoto_xml_is_valid(vals):
    fn, validity = vals
    xml = fixture_path(fn)
    result = rocoto.validate_rocoto_xml(input_xml=xml)
    assert result is validity


def test__write_rocoto_xml(tmp_path):
    cfgfile = fixture_path("hello_workflow.yaml")
    outfile = tmp_path / "rocoto.xml"
    rocoto._write_rocoto_xml(config_file=cfgfile, output_file=outfile)
    expected = fixture_path("hello_workflow.xml")
    assert compare_files(expected, outfile) is True
