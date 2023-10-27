# pylint: disable=missing-function-docstring,protected-access
"""
Tests for uwtools.rocoto module.
"""

import shutil
from unittest.mock import patch

import pytest

from uwtools import rocoto
from uwtools.tests.support import fixture_path

# Test functions


def test_realize_rocoto_default_output():
    cfgfile = fixture_path("hello_workflow.yaml")
    with patch.object(rocoto, "validate_rocoto_xml", value=True):
        assert rocoto.realize_rocoto_xml(config_file=cfgfile) is True


def test_realize_rocoto_invalid_xml(tmp_path):
    cfgfile = fixture_path("hello_workflow.yaml")
    outfile = tmp_path / "rocoto.xml"
    dump = lambda _, dst: shutil.copyfile(fixture_path("rocoto_invalid.xml"), dst)
    with patch.object(rocoto._RocotoXML, "dump", dump):
        success = rocoto.realize_rocoto_xml(config_file=cfgfile, output_file=outfile)
    assert success is False


@pytest.mark.parametrize("vals", [("hello_workflow.xml", True), ("rocoto_invalid.xml", False)])
def test_validate_rocoto_xml(vals):
    fn, validity = vals
    xml = fixture_path(fn)
    result = rocoto.validate_rocoto_xml(input_xml=xml)
    assert result is validity
