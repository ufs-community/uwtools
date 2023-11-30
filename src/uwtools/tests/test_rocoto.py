# pylint: disable=missing-function-docstring,protected-access,redefined-outer-name
"""
Tests for uwtools.rocoto module.
"""

import shutil
from typing import Callable, List
from unittest.mock import DEFAULT as D
from unittest.mock import PropertyMock, patch

import pytest
import yaml
from lxml import etree
from pytest import fixture, raises

from uwtools import rocoto
from uwtools.config.validator import _validation_errors
from uwtools.exceptions import UWConfigError
from uwtools.tests.support import fixture_path
from uwtools.utils.file import resource_pathobj

# Fixtures


@fixture
def assets(tmp_path):
    return fixture_path("hello_workflow.yaml"), tmp_path / "rocoto.xml"


# Helpers


def validator(*args) -> Callable:
    with open(resource_pathobj("rocoto.jsonschema"), "r", encoding="utf-8") as f:
        schema = yaml.safe_load(f)
    for arg in args:
        schema = {"$defs": schema["$defs"], **schema[arg]}
    return lambda config: "\n".join(str(x) for x in _validation_errors(config, schema))


# Tests


def test_realize_rocoto_invalid_xml(assets):
    cfgfile, outfile = assets
    with open(fixture_path("hello_workflow.xml"), "r", encoding="utf-8") as f:
        e = etree.parse(f)
    cycledef = e.xpath("/workflow/cycledef")[0]
    cycledef.getparent().remove(cycledef)
    invalid = outfile.parent / "bad.xml"
    with open(invalid, "w", encoding="utf-8") as f:
        f.write(etree.tostring(e).decode())
    dump = lambda _, dst: shutil.copyfile(str(invalid), dst)
    with patch.object(rocoto._RocotoXML, "dump", dump):
        assert rocoto.realize_rocoto_xml(config_file=cfgfile, output_file=outfile) is False


def test_realize_rocoto_xml_to_file(assets):
    cfgfile, outfile = assets
    assert rocoto.realize_rocoto_xml(config_file=cfgfile, output_file=outfile) is True


def test_realize_rocoto_xml_to_stdout(capsys, assets):
    cfgfile, outfile = assets
    assert rocoto.realize_rocoto_xml(config_file=cfgfile) is True
    with open(outfile, "w", encoding="utf-8") as f:
        f.write(capsys.readouterr().out)
    assert rocoto.validate_rocoto_xml(outfile)


def test_validate_rocoto_xml():
    assert rocoto.validate_rocoto_xml(input_xml=fixture_path("hello_workflow.xml")) is True


class Test__RocotoXML:
    """
    Tests for class uwtools.rocoto._RocotoXML.
    """

    @fixture
    def instance(self, assets):
        cfgfile, _ = assets
        return rocoto._RocotoXML(config_file=cfgfile)

    @fixture
    def root(self):
        return rocoto.Element("root")

    def test__add_metatask(self, instance, root):
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

    def test__add_task(self, instance, root):
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

    def test__add_task_dependency(self, instance, root):
        config = {"taskdep": {"attrs": {"task": "foo"}}}
        instance._add_task_dependency(e=root, config=config)
        dependency = root[0]
        assert dependency.tag == "dependency"
        taskdep = dependency[0]
        assert taskdep.tag == "taskdep"
        assert taskdep.get("task") == "foo"

    def test__add_task_dependency_and(self, instance, root):
        config = {"and": {"or_get_obs": {"datadep": {"attrs": {"age": "120"}}}}}
        instance._add_task_dependency(e=root, config=config)
        dependency = root[0]
        assert dependency.tag == "dependency"
        and_ = dependency[0]
        assert and_.tag == "and"
        assert and_.getchildren()[0].getchildren()[0].get("age") == "120"

    def test__add_task_dependency_fail(self, instance, root):
        config = {"unrecognized": "whatever"}
        with raises(UWConfigError):
            instance._add_task_dependency(e=root, config=config)

    @pytest.mark.parametrize(
        "config",
        [{"datadep": {"attrs": {"age": "120"}}}, {"timedep": {"attrs": {"offset": "&DEADLINE;"}}}],
    )
    def test__add_task_dependency_operand(self, config, instance, root):
        instance._add_task_dependency_operand_operator(e=root, config=config)
        element = root[0]
        for tag, block in config.items():
            assert tag == element.tag
            for attr, val in block["attrs"].items():
                assert element.get(attr) == val

    def test__add_task_dependency_operand_fail(self, instance, root):
        config = {"and": {"unrecognized": "whatever"}}
        with raises(UWConfigError):
            instance._add_task_dependency(e=root, config=config)

    @pytest.mark.parametrize(
        "config",
        [
            {"and": {"or": {"datadep": {"attrs": {"age": "120"}}}}},
            {"and": {"strneq": {"attrs": {"left": "&RUN_GSI;", "right": "YES"}}}},
        ],
    )
    def test__add_task_dependency_operator(self, config, instance, root):
        instance._add_task_dependency_operand_operator(e=root, config=config)
        for tag, _ in config.items():
            assert tag == next(iter(config))

    def test__add_task_dependency_streq(self, instance, root):
        config = {"streq": {"attrs": {"left": "&RUN_GSI;", "right": "YES"}}}
        instance._add_task_dependency(e=root, config=config)
        dependency = root[0]
        assert dependency.tag == "dependency"
        streq = dependency[0]
        assert streq.tag == "streq"
        assert streq.get("left") == "&RUN_GSI;"

    @pytest.mark.parametrize(
        "config",
        [
            ("streq", {"attrs": {"left": "&RUN_GSI;", "right": "YES"}}),
            ("strneq", {"attrs": {"left": "&RUN_GSI;", "right": "YES"}}),
        ],
    )
    def test__add_task_dependency_strequality(self, config, instance, root):
        tag, block = config
        instance._add_task_dependency_strequality(e=root, block=block, tag=tag)
        element = root[0]
        assert tag == element.tag
        for attr, val in block["attrs"].items():
            assert element.get(attr) == val

    def test__config_validate(self, assets, instance):
        cfgfile, _ = assets
        instance._config_validate(config_file=cfgfile)

    def test__config_validate_fail(self, instance, tmp_path):
        cfgfile = tmp_path / "bad.yaml"
        with open(cfgfile, "w", encoding="utf-8") as f:
            print("not: ok", file=f)
        with raises(UWConfigError):
            instance._config_validate(config_file=cfgfile)

    def test__add_task_envar(self, instance, root):
        instance._add_task_envar(root, "foo", "bar")
        envar = root[0]
        name, value = envar
        assert name.tag == "name"
        assert name.text == "foo"
        assert value.tag == "value"
        assert value.text == "bar"

    def test__add_workflow(self, instance):
        config = {
            "workflow": {
                "attrs": {"foo": "1", "bar": "2"},
                "cycledef": "3",
                "log": "4",
                "tasks": "5",
            }
        }
        with patch.multiple(
            instance, _add_workflow_cycledef=D, _add_workflow_log=D, _add_workflow_tasks=D
        ) as mocks:
            instance._add_workflow(config=config)
        workflow = instance._root
        assert workflow.tag == "workflow"
        assert workflow.get("foo") == "1"
        assert workflow.get("bar") == "2"
        mocks["_add_workflow_cycledef"].assert_called_once_with(workflow, "3")
        mocks["_add_workflow_log"].assert_called_once_with(workflow, config["workflow"])
        mocks["_add_workflow_tasks"].assert_called_once_with(workflow, "5")

    def test__add_workflow_cycledef(self, instance, root):
        config: List[dict] = [
            {"attrs": {"group": "g1"}, "spec": "t1"},
            {"attrs": {"group": "g2"}, "spec": "t2"},
        ]
        instance._add_workflow_cycledef(e=root, config=config)
        for i, item in enumerate(config):
            assert root[i].get("group") == item["attrs"]["group"]
            assert root[i].tag == "cycledef"
            assert root[i].text == item["spec"]

    def test__add_workflow_log_basic(self, instance, root):
        val = "/path/to/logfile"
        instance._add_workflow_log(e=root, config={"log": val})
        log = root[0]
        assert log.tag == "log"
        assert log.text == val

    def test__add_workflow_log_cyclestr(self, instance, root):
        val = "/path/to/logfile-@Y@m@d@H"
        instance._add_workflow_log(e=root, config={"log": {"cyclestr": {"value": val}}})
        log = root[0]
        assert log.tag == "log"
        assert log.xpath("cyclestr")[0].text == val

    def test__add_workflow_tasks(self, instance, root):
        config = {"metatask_foo": "1", "task_bar": "2"}
        with patch.multiple(instance, _add_metatask=D, _add_task=D) as mocks:
            instance._add_workflow_tasks(e=root, config=config)
        mocks["_add_metatask"].assert_called_once_with(root, "1", "foo")
        mocks["_add_task"].assert_called_once_with(root, "2", "bar")

    def test__doctype_entities(self, instance):
        assert '<!ENTITY ACCOUNT "myaccount">' in instance._doctype
        assert '<!ENTITY FOO "test.log">' in instance._doctype

    def test__doctype_entities_none(self, instance):
        del instance._config["workflow"]["entities"]
        assert instance._doctype is None

    def test__insert_doctype(self, instance):
        with patch.object(rocoto._RocotoXML, "_doctype", new_callable=PropertyMock) as _doctype:
            _doctype.return_value = "bar"
            assert instance._insert_doctype("foo\nbaz\n") == "foo\nbar\nbaz\n"

    def test__insert_doctype_none(self, instance):
        with patch.object(rocoto._RocotoXML, "_doctype", new_callable=PropertyMock) as _doctype:
            _doctype.return_value = None
            assert instance._insert_doctype("foo\nbaz\n") == "foo\nbaz\n"

    def test__set_and_render_jobname(self, instance):
        config = {"foo": "{{ jobname }}", "baz": "{{ qux }}"}
        assert instance._set_and_render_jobname(config=config, taskname="bar") == {
            "jobname": "bar",  # set
            "foo": "bar",  # rendered
            "baz": "{{ qux }}",  # ignored
        }

    def test__setattrs(self, instance, root):
        config = {"attrs": {"foo": "1", "bar": "2"}}
        instance._set_attrs(e=root, config=config)
        assert root.get("foo") == "1"
        assert root.get("bar") == "2"

    def test__tag_name(self, instance):
        assert instance._tag_name("foo") == ("foo", "")
        assert instance._tag_name("foo_bar") == ("foo", "bar")
        assert instance._tag_name("foo_bar_baz") == ("foo", "bar_baz")


# Schema tests


def test_schema_compoundTimeString():
    errors = validator("$defs", "compoundTimeString")
    # Just a string is ok:
    assert not errors("foo")
    # Non-string types are not ok:
    assert "88 is not valid" in errors(88)
    # A simple cycle string is ok:
    assert not errors({"cyclestr": {"value": "@Y@m@d@H"}})
    # The "value" entry is required:
    assert "is not valid" in errors({"cyclestr": {}})
    # Unknown properties are not allowed:
    assert "is not valid" in errors({"cyclestr": {"foo": "bar"}})
    # An "offset" attribute may be provided:
    assert not errors({"cyclestr": {"value": "@Y@m@d@H", "attrs": {"offset": "06:00:00"}}})
    # The "offset" value must be a valid time string:
    assert "is not valid" in errors({"cyclestr": {"value": "@Y@m@d@H", "attrs": {"offset": "x"}}})


def test_schema_workflow_cycledef():
    errors = validator("properties", "workflow", "properties", "cycledef")
    # Basic spec:
    spec = "202311291200 202312011200 06:00:00"
    assert not errors([{"spec": spec}])
    # Spec with step specified as seconds:
    assert not errors([{"spec": "202311291200 202312011200 3600"}])
    # Basic spec with group attribute:
    assert not errors([{"attrs": {"group": "g"}, "spec": spec}])
    # Spec with positive activation offset attribute:
    assert not errors([{"attrs": {"activation_offset": "12:00:00"}, "spec": spec}])
    # Spec with negative activation offset attribute:
    assert not errors([{"attrs": {"activation_offset": "-12:00:00"}, "spec": spec}])
    # Spec with activation offset specified as positive seconds:
    assert not errors([{"attrs": {"activation_offset": "3600"}, "spec": spec}])
    # Spec with activation offset specified as negative seconds:
    assert not errors([{"attrs": {"activation_offset": "-3600"}, "spec": spec}])
    # Property spec is required:
    assert "'spec' is a required property" in errors([{}])
    # Additional properties are not allowed:
    assert "'foo' was unexpected" in errors([{"spec": spec, "foo": "bar"}])
    # Additional attributes are not allowed:
    assert "'foo' was unexpected" in errors([{"attrs": {"foo": "bar"}, "spec": spec}])
    # Bad spec:
    assert "'x 202312011200 06:00:00' is not valid" in errors([{"spec": "x 202312011200 06:00:00"}])
    # Spec with bad activation offset attribute:
    assert "'foo' is not valid" in errors([{"attrs": {"activation_offset": "foo"}, "spec": spec}])
