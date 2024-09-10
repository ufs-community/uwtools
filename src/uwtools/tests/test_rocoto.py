# pylint: disable=missing-function-docstring,protected-access,redefined-outer-name
"""
Tests for uwtools.rocoto module.
"""

from unittest.mock import DEFAULT as D
from unittest.mock import PropertyMock, patch

from lxml import etree
from pytest import fixture, mark, raises

from uwtools import rocoto
from uwtools.config.formats.yaml import YAMLConfig
from uwtools.exceptions import UWConfigError, UWError
from uwtools.tests.support import fixture_path

# Fixtures


@fixture
def assets(tmp_path):
    return fixture_path("hello_workflow.yaml"), tmp_path / "rocoto.xml"


@fixture
def validation_assets(tmp_path):
    xml_file_good = fixture_path("hello_workflow.xml")
    with open(xml_file_good, "r", encoding="utf-8") as f:
        xml_string_good = f.read()
    xml_string_bad = "<bad/>"
    xml_file_bad = tmp_path / "bad.xml"
    with open(xml_file_bad, "w", encoding="utf-8") as f:
        print(xml_string_bad, file=f)
    return xml_file_bad, xml_file_good, xml_string_bad, xml_string_good


# Tests


def test_realize_rocoto_invalid_xml(assets):
    cfgfile, outfile = assets
    with patch.object(rocoto, "validate_rocoto_xml_string") as vrxs:
        vrxs.return_value = False
        with raises(UWError):
            rocoto.realize_rocoto_xml(config=cfgfile, output_file=outfile)


def test_realize_rocoto_xml_cfg_to_file(assets):
    cfgfile, outfile = assets
    rocoto.realize_rocoto_xml(config=YAMLConfig(cfgfile), output_file=outfile)
    assert rocoto.validate_rocoto_xml_file(xml_file=outfile)


def test_realize_rocoto_xml_file_to_file(assets):
    cfgfile, outfile = assets
    rocoto.realize_rocoto_xml(config=cfgfile, output_file=outfile)
    assert rocoto.validate_rocoto_xml_file(xml_file=outfile)


def test_realize_rocoto_xml_cfg_to_stdout(capsys, assets):
    cfgfile, outfile = assets
    rocoto.realize_rocoto_xml(config=YAMLConfig(cfgfile))
    with open(outfile, "w", encoding="utf-8") as f:
        f.write(capsys.readouterr().out)
    assert rocoto.validate_rocoto_xml_file(xml_file=outfile)


def test_realize_rocoto_xml_file_to_stdout(capsys, assets):
    cfgfile, outfile = assets
    rocoto.realize_rocoto_xml(config=cfgfile)
    with open(outfile, "w", encoding="utf-8") as f:
        f.write(capsys.readouterr().out)
    assert rocoto.validate_rocoto_xml_file(xml_file=outfile)


def test_validate_rocoto_xml_file_fail(validation_assets):
    xml_file_bad, _, _, _ = validation_assets
    assert rocoto.validate_rocoto_xml_file(xml_file=xml_file_bad) is False


def test_validate_rocoto_xml_file_pass(validation_assets):
    _, xml_file_good, _, _ = validation_assets
    assert rocoto.validate_rocoto_xml_file(xml_file=xml_file_good) is True


def test_validate_rocoto_xml_string_fail(validation_assets):
    _, _, xml_string_bad, _ = validation_assets
    assert rocoto.validate_rocoto_xml_string(xml=xml_string_bad) is False


def test_validate_rocoto_xml_string_pass(validation_assets):
    _, _, _, xml_string_good = validation_assets
    assert rocoto.validate_rocoto_xml_string(xml=xml_string_good) is True


class Test__RocotoXML:
    """
    Tests for class uwtools.rocoto._RocotoXML.
    """

    @fixture
    def instance(self, assets):
        cfgfile, _ = assets
        return rocoto._RocotoXML(config=cfgfile)

    @fixture
    def root(self):
        return rocoto.Element("root")

    def test_instantiate_from_cfgobj(self, assets):
        cfgfile, _ = assets
        assert rocoto._RocotoXML(config=YAMLConfig(cfgfile))._root.tag == "workflow"

    @mark.parametrize("config", ["bar", 42])
    def test__add_compound_time_string_basic(self, config, instance, root):
        instance._add_compound_time_string(e=root, config=config, tag="foo")
        child = root[0]
        assert child.tag == "foo"
        assert child.text == str(config)

    def test__add_compound_time_string_cyclestr(self, instance, root):
        config = {"cyclestr": {"attrs": {"baz": "42"}, "value": "qux"}}
        instance._add_compound_time_string(e=root, config=config, tag="foo")
        cyclestr = root[0][0]
        assert cyclestr.get("baz") == "42"
        assert cyclestr.text == "qux"

    def test__add_compound_time_string_list(self, instance, root):
        config = [
            "cycle-",
            {"cyclestr": {"value": "%s"}},
            "-valid-",
            {"cyclestr": {"value": "%s", "attrs": {"offset": "00:06:00"}}},
            ".log",
        ]
        xml = "<a>{}</a>".format(
            "".join(
                [
                    "cycle-",
                    "<cyclestr>%s</cyclestr>",
                    "-valid-",
                    '<cyclestr offset="00:06:00">%s</cyclestr>',
                    ".log",
                ]
            )
        )
        instance._add_compound_time_string(e=root, config=config, tag="a")
        assert etree.tostring(root[0]).decode("utf-8") == xml

    def test__add_metatask(self, instance, root):
        config = {
            "metatask_foo": "1",
            "attrs": {"mode": "parallel", "throttle": 42},
            "task_bar": "2",
            "var": {"baz": "3", "qux": "4"},
        }
        taskname = "test-metatask"
        orig = instance._add_metatask
        with patch.multiple(instance, _add_metatask=D, _add_task=D) as mocks:
            orig(e=root, config=config, name_attr=taskname)
        metatask = root[0]
        assert metatask.tag == "metatask"
        assert metatask.get("mode") == "parallel"
        assert metatask.get("name") == taskname
        assert metatask.get("throttle") == "42"
        assert {e.get("name"): e.text for e in metatask.xpath("var")} == {"baz": "3", "qux": "4"}
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
            instance._add_task(e=root, config=config, name_attr=taskname)
        task = root[0]
        assert task.tag == "task"
        assert task.get("name") == taskname
        assert task.get("foo") == "1"
        assert task.get("bar") == "2"
        mocks["_add_task_dependency"].assert_called_once_with(task, "qux")
        mocks["_add_task_envar"].assert_called_once_with(task, "A", "apple")

    @mark.parametrize("cores", [1, "1"])
    def test__add_task_cores_int_or_str(self, cores, instance, root):
        # Ensure that either int or str "cores" values are accepted.
        config = {"command": "c", "cores": cores, "walltime": "00:00:01"}
        instance._add_task(e=root, config=config, name_attr="foo")

    def test__add_task_dependency_and(self, instance, root):
        config = {"and": {"or_get_obs": {"taskdep": {"attrs": {"task": "foo"}}}}}
        instance._add_task_dependency(e=root, config=config)
        dependency = root[0]
        assert dependency.tag == "dependency"
        and_ = dependency[0]
        assert and_.tag == "and"
        assert and_.xpath("or[1]/taskdep")[0].get("task") == "foo"

    @mark.parametrize(
        "value",
        ["/some/file", {"cyclestr": {"value": "@Y@m@d@H", "attrs": {"offset": "06:00:00"}}}],
    )
    def test__add_task_dependency_datadep(self, instance, root, value):
        age = "00:00:02:00"
        minsize = "1K"
        config = {"datadep": {"attrs": {"age": age, "minsize": minsize}, "value": value}}
        instance._add_task_dependency(e=root, config=config)
        dependency = root[0]
        assert dependency.tag == "dependency"
        child = dependency[0]
        assert child.tag == "datadep"
        assert child.get("age") == age
        assert child.get("minsize") == minsize
        assert child.text == value if isinstance(value, str) else value["cyclestr"]["value"]

    def test__add_task_dependency_fail(self, instance, root):
        config = {"unrecognized": "whatever"}
        with raises(UWConfigError):
            instance._add_task_dependency(e=root, config=config)

    def test__add_task_dependency_fail_bad_operand(self, instance, root):
        config = {"and": {"unrecognized": "whatever"}}
        with raises(UWConfigError):
            instance._add_task_dependency(e=root, config=config)

    def test__add_task_dependency_metataskdep(self, instance, root):
        config = {"metataskdep": {"attrs": {"metatask": "foo"}}}
        instance._add_task_dependency(e=root, config=config)
        dependency = root[0]
        assert dependency.tag == "dependency"
        child = dependency[0]
        assert child.tag == "metataskdep"
        assert child.get("metatask") == "foo"

    @mark.parametrize(
        "tag_config",
        [("and", {"strneq": {"attrs": {"left": "&RUN_GSI;", "right": "YES"}}})],
    )
    def test__add_task_dependency_operator(self, instance, root, tag_config):
        tag, config = tag_config
        instance._add_task_dependency_child(e=root, config=config, tag=tag)
        for tag, _ in config.items():
            assert tag == next(iter(config))

    def test__add_task_dependency_operator_datadep_operand(self, instance, root):
        value = "/some/file"
        config = {"value": value}
        instance._add_task_dependency_child(e=root, config=config, tag="datadep")
        e = root[0]
        assert e.tag == "datadep"
        assert e.text == value

    def test__add_task_dependency_operator_task_operand(self, instance, root):
        taskname = "some-task"
        config = {"attrs": {"task": taskname}}
        instance._add_task_dependency_child(e=root, config=config, tag="taskdep")
        e = root[0]
        assert e.tag == "taskdep"
        assert e.get("task") == taskname

    def test__add_task_dependency_operator_timedep_operand(self, instance, root):
        value = 20230103120000
        config = value
        instance._add_task_dependency_child(e=root, config=config, tag="timedep")
        e = root[0]
        assert e.tag == "timedep"
        assert e.text == str(value)

    def test__add_task_dependency_sh(self, instance, root):
        config = {"sh_foo": {"attrs": {"runopt": "-c", "shell": "/bin/bash"}, "command": "ls"}}
        instance._add_task_dependency(e=root, config=config)
        dependency = root[0]
        assert dependency.tag == "dependency"
        sh = dependency[0]
        assert sh.tag == "sh"
        assert sh.get("name") == "foo"
        assert sh.get("runopt") == "-c"
        assert sh.get("shell") == "/bin/bash"
        assert sh.text == "ls"

    def test__add_task_dependency_streq(self, instance, root):
        config = {"streq": {"attrs": {"left": "&RUN_GSI;", "right": "YES"}}}
        instance._add_task_dependency(e=root, config=config)
        dependency = root[0]
        assert dependency.tag == "dependency"
        streq = dependency[0]
        assert streq.tag == "streq"
        assert streq.get("left") == "&RUN_GSI;"

    @mark.parametrize(
        "config",
        [
            ("streq", {"attrs": {"left": "&RUN_GSI;", "right": "YES"}}),
            ("strneq", {"attrs": {"left": "&RUN_GSI;", "right": "YES"}}),
        ],
    )
    def test__add_task_dependency_strequality(self, config, instance, root):
        tag, config = config
        instance._add_task_dependency_strequality(e=root, config=config, tag=tag)
        element = root[0]
        assert tag == element.tag
        for attr, val in config["attrs"].items():
            assert element.get(attr) == val

    def test__add_task_dependency_taskdep(self, instance, root):
        config = {"taskdep": {"attrs": {"task": "foo"}}}
        instance._add_task_dependency(e=root, config=config)
        dependency = root[0]
        assert dependency.tag == "dependency"
        child = dependency[0]
        assert child.tag == "taskdep"
        assert child.get("task") == "foo"

    def test__add_task_dependency_taskvalid(self, instance, root):
        config = {"taskvalid": {"attrs": {"task": "foo"}}}
        instance._add_task_dependency(e=root, config=config)
        dependency = root[0]
        assert dependency.tag == "dependency"
        taskvalid = dependency[0]
        assert taskvalid.tag == "taskvalid"
        assert taskvalid.get("task") == "foo"

    @mark.parametrize(
        "value",
        [
            "202301031200",
            202301031200,
            {"cyclestr": {"value": "@Y@m@d@H", "attrs": {"offset": "06:00:00"}}},
        ],
    )
    def test__add_task_dependency_timedep(self, instance, root, value):
        config = {"timedep": value}
        instance._add_task_dependency(e=root, config=config)
        dependency = root[0]
        assert dependency.tag == "dependency"
        child = dependency[0]
        assert child.tag == "timedep"
        if isinstance(value, dict):
            assert child.xpath("cyclestr")[0].text == value["cyclestr"]["value"]
        else:
            assert child.text == str(value)

    def test__config_validate_config(self, assets, instance):
        cfgfile, _ = assets
        instance._config_validate(config=YAMLConfig(cfgfile))

    def test__config_validate_file(self, assets, instance):
        cfgfile, _ = assets
        instance._config_validate(config=cfgfile)

    def test__config_validate_config_fail(self, instance, tmp_path):
        cfgfile = tmp_path / "bad.yaml"
        with open(cfgfile, "w", encoding="utf-8") as f:
            print("not: ok", file=f)
        with raises(UWConfigError):
            instance._config_validate(config=YAMLConfig(cfgfile))

    def test__config_validate_file_fail(self, instance, tmp_path):
        cfgfile = tmp_path / "bad.yaml"
        with open(cfgfile, "w", encoding="utf-8") as f:
            print("not: ok", file=f)
        with raises(UWConfigError):
            instance._config_validate(config=cfgfile)

    def test__add_task_envar(self, instance, root):
        instance._add_task_envar(root, "foo", "bar")
        envar = root[0]
        name, value = envar
        assert name.tag == "name"
        assert name.text == "foo"
        assert value.tag == "value"
        assert value.text == "bar"

    def test__add_task_envar_compound(self, instance, root):
        instance._add_task_envar(root, "foo", {"cyclestr": {"value": "bar_@Y"}})
        envar = root[0]
        name, value = envar
        child = value[0]
        assert name.tag == "name"
        assert name.text == "foo"
        assert value.tag == "value"
        assert value.text is None
        assert child.text == "bar_@Y"

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
        config: list[dict] = [
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

    def test__setattrs(self, instance, root):
        config = {"attrs": {"foo": "1", "bar": "2"}}
        instance._set_attrs(e=root, config=config)
        assert root.get("foo") == "1"
        assert root.get("bar") == "2"

    def test__set_and_render_jobname(self, instance):
        config = {"join": "{{jobname}}.log"}
        cfg = instance._set_and_render_jobname(config, "foo")
        assert cfg["join"] == "foo.log"
        assert cfg["jobname"] == "foo"

    def test__tag_name(self, instance):
        assert instance._tag_name("foo") == ("foo", "")
        assert instance._tag_name("foo_bar") == ("foo", "bar")
        assert instance._tag_name("foo_bar_baz") == ("foo", "bar_baz")

    def test_dump(self, instance, tmp_path):
        path = tmp_path / "out.xml"
        instance.dump(path=path)
        assert rocoto.validate_rocoto_xml_file(path)
