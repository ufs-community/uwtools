# pylint: disable=missing-function-docstring,protected-access,redefined-outer-name
"""
Tests for uwtools.rocoto module.
"""

import shutil
from unittest.mock import patch

import pytest
from pytest import fixture

from uwtools import rocoto
from uwtools.tests.support import fixture_path

# Fixtures


@fixture
def realize_rocoto_xml_assets(tmp_path):
    return fixture_path("hello_workflow.yaml"), tmp_path / "rocoto.xml"


# Tests


def test_realize_rocoto_xml_to_file(realize_rocoto_xml_assets):
    cfgfile, outfile = realize_rocoto_xml_assets
    assert rocoto.realize_rocoto_xml(config_file=cfgfile, output_file=outfile) is True


def test_realize_rocoto_xml_to_stdout(capsys, realize_rocoto_xml_assets):
    cfgfile, outfile = realize_rocoto_xml_assets
    assert rocoto.realize_rocoto_xml(config_file=cfgfile) is True
    with open(outfile, "w", encoding="utf-8") as f:
        f.write(capsys.readouterr().out)
    assert rocoto.validate_rocoto_xml(outfile)


def test_realize_rocoto_invalid_xml(realize_rocoto_xml_assets):
    cfgfile, outfile = realize_rocoto_xml_assets
    dump = lambda _, dst: shutil.copyfile(fixture_path("rocoto_invalid.xml"), dst)
    with patch.object(rocoto._RocotoXML, "dump", dump):
        assert rocoto.realize_rocoto_xml(config_file=cfgfile, output_file=outfile) is False


@pytest.mark.parametrize("vals", [("hello_workflow.xml", True), ("rocoto_invalid.xml", False)])
def test_validate_rocoto_xml(vals):
    fn, validity = vals
    xml = fixture_path(fn)
    assert rocoto.validate_rocoto_xml(input_xml=xml) is validity
