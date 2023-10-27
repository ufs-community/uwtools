# pylint: disable=missing-function-docstring,protected-access,redefined-outer-name
"""
Tests for uwtools.rocoto module.
"""

import shutil
from unittest.mock import DEFAULT as D
from unittest.mock import patch

import pytest
from pytest import fixture, raises

from uwtools import rocoto
from uwtools.exceptions import UWConfigError
from uwtools.tests.support import fixture_path

# Fixtures


@fixture
def assets(tmp_path):
    return fixture_path("hello_workflow.yaml"), tmp_path / "rocoto.xml"


@fixture
def instance(assets):
    cfgfile, _ = assets
    return rocoto._RocotoXML(config_file=cfgfile)


@fixture
def root():
    return rocoto.Element("root")


# Tests


def test_realize_rocoto_xml_to_file(assets):
    cfgfile, outfile = assets
    assert rocoto.realize_rocoto_xml(config_file=cfgfile, output_file=outfile) is True


def test_realize_rocoto_xml_to_stdout(capsys, assets):
    cfgfile, outfile = assets
    assert rocoto.realize_rocoto_xml(config_file=cfgfile) is True
    with open(outfile, "w", encoding="utf-8") as f:
        f.write(capsys.readouterr().out)
    assert rocoto.validate_rocoto_xml(outfile)


def test_realize_rocoto_invalid_xml(assets):
    cfgfile, outfile = assets
    dump = lambda _, dst: shutil.copyfile(fixture_path("rocoto_invalid.xml"), dst)
    with patch.object(rocoto._RocotoXML, "dump", dump):
        assert rocoto.realize_rocoto_xml(config_file=cfgfile, output_file=outfile) is False


@pytest.mark.parametrize("vals", [("hello_workflow.xml", True), ("rocoto_invalid.xml", False)])
def test_validate_rocoto_xml(vals):
    fn, validity = vals
    xml = fixture_path(fn)
    assert rocoto.validate_rocoto_xml(input_xml=xml) is validity


def test__RocotoXML__doctype_entities(instance):
    assert '<!ENTITY ACCOUNT "myaccount">' in instance._doctype
    assert '<!ENTITY FOO "test.log">' in instance._doctype


def test__RocotoXML__doctype_entities_none(instance):
    del instance._config["workflow"]["entities"]
    assert instance._doctype is None


def test__RocotoXML__config_validate(assets, instance):
    cfgfile, _ = assets
    instance._config_validate(config_file=cfgfile)


def test__RocotoXML__config_validate_fail(instance, tmp_path):
    cfgfile = tmp_path / "bad.yaml"
    with open(cfgfile, "w", encoding="utf-8") as f:
        print("not: ok", file=f)
    with raises(UWConfigError):
        instance._config_validate(config_file=cfgfile)


def test__RocotoXML__add_metatask(instance, root):
    config = {"metatask_foo": "1", "task_bar": "2", "var": {"baz": "3", "qux": "4"}}
    taskname = "test-metatask"
    orig = instance._add_metatask
    with patch.multiple(instance, _add_metatask=D, _add_task=D) as mocks:
        orig(e=root, config=config, taskname=taskname)
    metatask = root[0]
    assert metatask.tag == "metatask"
    assert metatask.get("name") == taskname
    mocks["_add_metatask"].assert_called_once_with(metatask, "1", "foo")
    mocks["_add_task"].assert_called_once_with(metatask, "2", "bar")


def test__RocotoXML__add_task(instance, root):
    config = {
        "attrs": {"foo": "1", "bar": "2"},
        "account": "baz",
        "dependency": "qux",
        "envars": {"A": "apple"},
    }
    taskname = "test-task"
    with patch.multiple(instance, _add_task_dependency=D, _add_task_envar=D) as mocks:
        instance._add_task(e=root, config=config, taskname=taskname)
    task = root[0]
    assert task.tag == "task"
    assert task.get("name") == taskname
    assert task.get("foo") == "1"
    assert task.get("bar") == "2"
    mocks["_add_task_dependency"].assert_called_once_with(task, "qux")
    mocks["_add_task_envar"].assert_called_once_with(task, "A", "apple")


def test__RocotoXML__add_task_dependency(instance, root):
    config = {"taskdep": {"attrs": {"task": "foo"}}}
    instance._add_task_dependency(e=root, config=config)
    dependency = root[0]
    assert dependency.tag == "dependency"
    taskdep = dependency[0]
    assert taskdep.tag == "taskdep"
    assert taskdep.get("task") == "foo"


def test__RocotoXML__add_task_dependency_fail(instance, root):
    config = {"unrecognized": "whatever"}
    with raises(UWConfigError):
        instance._add_task_dependency(e=root, config=config)
