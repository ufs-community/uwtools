"""
Tests for uwtools.rocoto module.
"""

import sqlite3
from contextlib import contextmanager
from unittest.mock import DEFAULT as D
from unittest.mock import Mock, PropertyMock, patch

from lxml import etree
from pytest import fixture, mark, raises

from uwtools import rocoto
from uwtools.config.formats.yaml import YAMLConfig
from uwtools.exceptions import UWConfigError, UWError
from uwtools.tests.support import fixture_path, schema_validator

# Fixtures


@fixture
def assets(tmp_path):
    return fixture_path("hello_workflow.yaml"), tmp_path / "rocoto.xml"


@fixture
def rocoto_runner_args(utc, tmp_path):
    return {
        "cycle": utc(2025, 7, 21, 12),
        "database": tmp_path / "rocoto.db",
        "rate": 11,
        "task": "foo",
        "workflow": tmp_path / "rocoto.xml",
    }


@fixture
def validation_assets(tmp_path):
    xml_file_good = fixture_path("hello_workflow.xml")
    xml_string_good = xml_file_good.read_text()
    xml_string_bad = "<bad/>"
    xml_file_bad = tmp_path / "bad.xml"
    xml_file_bad.write_text(xml_string_bad)
    return xml_file_bad, xml_file_good, xml_string_bad, xml_string_good


# Tests


def test_rocoto_realize__rocoto_invalid_xml(assets):
    cfgfile, outfile = assets
    with patch.object(rocoto, "validate_string") as vrxs:
        vrxs.return_value = False
        with raises(UWError):
            rocoto.realize(config=cfgfile, output_file=outfile)


def test_rocoto_realize__cfg_to_file(assets):
    cfgfile, outfile = assets
    rocoto.realize(config=YAMLConfig(cfgfile), output_file=outfile)
    assert rocoto.validate_file(xml_file=outfile)


def test_rocoto_realize__file_to_file(assets):
    cfgfile, outfile = assets
    rocoto.realize(config=cfgfile, output_file=outfile)
    assert rocoto.validate_file(xml_file=outfile)


def test_rocoto_realize__cfg_to_stdout(capsys, assets):
    cfgfile, outfile = assets
    rocoto.realize(config=YAMLConfig(cfgfile))
    outfile.write_text(capsys.readouterr().out)
    assert rocoto.validate_file(xml_file=outfile)


def test_rocoto_realize__file_to_stdout(capsys, assets):
    cfgfile, outfile = assets
    rocoto.realize(config=cfgfile)
    outfile.write_text(capsys.readouterr().out)
    assert rocoto.validate_file(xml_file=outfile)


def test_rocoto_run(rocoto_runner_args):
    with patch.object(rocoto, "_RocotoRunner") as _RocotoRunner:  # noqa: N806
        rocoto.run(**rocoto_runner_args)
    _RocotoRunner.assert_called_once_with(*rocoto_runner_args.values())


def test_rocoto_validate__file_fail(validation_assets):
    xml_file_bad, _, _, _ = validation_assets
    assert rocoto.validate_file(xml_file=xml_file_bad) is False


def test_rocoto_validate__file_pass(validation_assets):
    _, xml_file_good, _, _ = validation_assets
    assert rocoto.validate_file(xml_file=xml_file_good) is True


def test_rocoto_validate__string_fail(validation_assets):
    _, _, xml_string_bad, _ = validation_assets
    assert rocoto.validate_string(xml=xml_string_bad) is False


def test_rocoto_validate__string_pass(validation_assets):
    _, _, _, xml_string_good = validation_assets
    assert rocoto.validate_string(xml=xml_string_good) is True


class TestRocotoRunner:
    """
    Tests for class uwtools.rocoto._RocotoRunner.
    """

    # Fixtures

    @fixture
    def instance(self, rocoto_runner_args):
        return rocoto._RocotoRunner(**rocoto_runner_args)

    # Helpers

    def check_mock_calls_counts(self, mocks, _iterate, _report, _state, sleep):
        assert mocks["_iterate"].call_count == _iterate
        assert mocks["_report"].call_count == _report
        assert mocks["_state"].call_count == _state
        assert mocks["sleep"].call_count == sleep

    def dbsetup(self, instance):
        instance._database.touch()
        columns = ", ".join(
            [
                "id integer primary key",
                "taskname varchar(64)",
                "cycle datetime",
                "state varchar(64)",
            ]
        )
        instance._cursor.execute(f"create table jobs ({columns});")

    @contextmanager
    def mocks(self):
        with (
            patch.object(rocoto, "sleep") as sleep,
            patch.object(rocoto._RocotoRunner, "_iterate") as _iterate,
            patch.object(rocoto._RocotoRunner, "_report") as _report,
            patch.object(rocoto._RocotoRunner, "_state", new_callable=PropertyMock) as _state,
        ):
            _iterate.return_value = True
            yield dict(sleep=sleep, _iterate=_iterate, _report=_report, _state=_state)

    # Tests

    def test_rocoto__RocotoRunner__init_and_del(self, rocoto_runner_args):
        rr = rocoto._RocotoRunner(**rocoto_runner_args)
        con = Mock()
        rr._con = con
        del rr
        con.close.assert_called_once_with()

    def test_rocoto__RocotoRunner_run__active(self, instance):
        with self.mocks() as mocks:
            mocks["_state"].side_effect = ["RUNNING", "COMPLETE"]
            assert instance.run() is True
            self.check_mock_calls_counts(mocks, _iterate=1, _report=1, _state=2, sleep=0)

    def test_rocoto__RocotoRunner_run__inactive(self, instance):
        with self.mocks() as mocks:
            mocks["_state"].side_effect = ["COMPLETE"]
            assert instance.run() is True
            self.check_mock_calls_counts(mocks, _iterate=0, _report=0, _state=1, sleep=0)

    def test_rocoto__RocotoRunner_run__transient(self, instance):
        with self.mocks() as mocks:
            mocks["_state"].side_effect = ["SUBMITTING", "RUNNING", "COMPLETE"]
            assert instance.run() is True
            self.check_mock_calls_counts(mocks, _iterate=1, _report=1, _state=3, sleep=0)

    def test_rocoto__RocotoRunner_run__iterate_failure(self, instance):
        instance._initialized = True
        with self.mocks() as mocks:
            mocks["_iterate"].return_value = False
            assert instance.run() is False
            self.check_mock_calls_counts(mocks, _iterate=1, _report=0, _state=0, sleep=0)

    def test_rocoto__RocotoRunner_run__sleeps(self, instance):
        with self.mocks() as mocks:
            mocks["_state"].side_effect = ["RUNNING", "RUNNING", "COMPLETE"]
            assert instance.run() is True
            self.check_mock_calls_counts(mocks, _iterate=2, _report=2, _state=3, sleep=1)

    def test_rocoto__RocotoRunner__connection(self, instance):
        instance._database.touch()
        assert isinstance(instance._connection, sqlite3.Connection)

    def test_rocoto__RocotoRunner__connection__no_file(self, instance):
        assert instance._connection is None

    def test_rocoto__RocotoRunner__cursor(self, instance):
        instance._database.touch()
        assert isinstance(instance._cursor, sqlite3.Cursor)

    def test_rocoto__RocotoRunner__cursor__no_file(self, instance):
        assert instance._cursor is None

    def test_rocoto__RocotoRunner__iterate(self, instance, logged):
        retval = (True, "")
        with patch.object(rocoto, "run_shell_cmd", return_value=retval) as run_shell_cmd:
            assert instance._iterate() is True
        run_shell_cmd.assert_called_once_with(
            "rocotorun -d %s -w %s" % (instance._database, instance._workflow), quiet=True
        )
        assert logged("Iterating workflow")

    def test_rocoto__RocotoRunner__query_data(self, instance):
        assert instance._query_data == {"taskname": "foo", "cycle": 1753099200}

    def test_rocoto__RocotoRunner__query_stmt(self, instance):
        assert (
            instance._query_stmt
            == "select state from jobs where taskname=:taskname and cycle=:cycle"
        )

    def test_rocoto__RocotoRunner__report(self, instance, logged):
        instance._database.touch()
        retval = (True, "foo\nbar\n")
        with patch.object(rocoto, "run_shell_cmd", return_value=retval) as run_shell_cmd:
            instance._report()
        for line in ["Workflow status:", "foo", "bar"]:
            assert logged(line)
        run_shell_cmd.assert_called_once_with(
            "rocotostat -d %s -w %s" % (instance._database, instance._workflow), quiet=True
        )

    def test_rocoto__RocotoRunner__state(self, instance):
        self.dbsetup(instance)
        instance._cursor.execute(
            "insert into jobs values (:id, :taskname, :cycle, :state)",
            {"id": 1, "taskname": "foo", "cycle": instance._cycle.timestamp(), "state": "COMPLETE"},
        )
        assert instance._state == "COMPLETE"

    def test_rocoto__RocotoRunner__state__none(self, instance):
        self.dbsetup(instance)
        assert instance._state is None


class TestRocotoXML:
    """
    Tests for class uwtools.rocoto._RocotoXML.
    """

    # Fixtures

    @fixture
    def instance(self, assets):
        cfgfile, _ = assets
        return rocoto._RocotoXML(config=cfgfile)

    @fixture
    def root(self):
        return rocoto.Element("root")

    # Tests

    def test__RocotoXML__instantiate_from_cfgobj(self, assets):
        cfgfile, _ = assets
        assert rocoto._RocotoXML(config=YAMLConfig(cfgfile))._root.tag == "workflow"

    def test_rocoto__RocotoXML_dump(self, instance, tmp_path):
        path = tmp_path / "out.xml"
        instance.dump(path=path)
        assert rocoto.validate_file(path)

    @mark.parametrize("config", ["bar", 42])
    def test_rocoto__RocotoXML__add_compound_time_string__basic(self, config, instance, root):
        instance._add_compound_time_string(e=root, config=config, tag="foo")
        child = root[0]
        assert child.tag == "foo"
        assert child.text == str(config)

    def test_rocoto__RocotoXML__add_compound_time_string__cyclestr(self, instance, root):
        config = {"cyclestr": {"attrs": {"offset": "00:05:00"}, "value": "qux"}}
        errors = schema_validator("rocoto", "$defs", "cycleString")
        assert not errors(config)
        instance._add_compound_time_string(e=root, config=config, tag="foo")
        cyclestr = root[0][0]
        assert cyclestr.get("offset") == "00:05:00"
        assert cyclestr.text == "qux"

    def test_rocoto__RocotoXML__add_compound_time_string__list(self, instance, root):
        config = [
            "cycle-",
            {"cyclestr": {"value": "%s"}},
            "-valid-",
            {"cyclestr": {"value": "%s", "attrs": {"offset": "00:06:00"}}},
            ".log",
        ]
        errors = schema_validator("rocoto", "$defs", "compoundTimeString")
        assert not errors(config)
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

    def test_rocoto__RocotoXML__add_metatask(self, instance, root):
        config = {
            "attrs": {"mode": "parallel", "throttle": 42},
            "var": {"baz": "3", "qux": "4"},
            "metatask_nest": {
                "var": {"bar": "1 2 3"},
                "task_bar": {
                    "cores": 2,
                    "walltime": "00:10:00",
                    "command": "echo hello",
                },
            },
        }
        errors = schema_validator("rocoto", "$defs")
        metataskname = "metatask_test"
        assert not errors({metataskname: config})
        orig = instance._add_metatask
        with patch.multiple(instance, _add_metatask=D, _add_task=D) as mocks:
            orig(e=root, config=config, name_attr=metataskname)
        metatask = root[0]
        assert metatask.tag == "metatask"
        assert metatask.get("mode") == "parallel"
        assert metatask.get("name") == metataskname
        assert metatask.get("throttle") == "42"
        assert {e.get("name"): e.text for e in metatask.xpath("var")} == {"baz": "3", "qux": "4"}
        mocks["_add_metatask"].assert_called_once_with(
            metatask,
            {
                "var": {"bar": "1 2 3"},
                "task_bar": {"cores": 2, "walltime": "00:10:00", "command": "echo hello"},
            },
            "nest",
        )

    def test_rocoto__RocotoXML__add_task(self, instance, root):
        config = {
            "attrs": {"foo": "1", "bar": "2"},
            "account": "baz",
            "dependency": {"taskdep": {"attrs": {"task": "task_foo"}}},
            "envars": {"A": "apple"},
            "walltime": "00:12:00",
            "command": "echo hello",
            "cores": 2,
        }
        taskname = "task_test"
        errors = schema_validator("rocoto", "$defs")
        assert not errors({taskname: config})
        with patch.multiple(instance, _add_task_dependency=D, _add_task_envar=D) as mocks:
            instance._add_task(e=root, config=config, name_attr=taskname)
        task = root[0]
        assert task.tag == "task"
        assert task.get("name") == taskname
        assert task.get("foo") == "1"
        assert task.get("bar") == "2"
        mocks["_add_task_dependency"].assert_called_once_with(
            task, {"taskdep": {"attrs": {"task": "task_foo"}}}
        )
        mocks["_add_task_envar"].assert_called_once_with(task, "A", "apple")

    @mark.parametrize("cores", [1, "1"])
    def test_rocoto__RocotoXML__add_task__cores_int_or_str(self, cores, instance, root):
        # Ensure that either int or str "cores" values are accepted.
        config = {"command": "c", "cores": cores, "walltime": "00:00:01"}
        instance._add_task(e=root, config=config, name_attr="foo")

    def test_rocoto__RocotoXML__add_task_dependency__and(self, instance, root):
        config = {"and": {"or_get_obs": {"taskdep": {"attrs": {"task": "foo"}}}}}
        errors = schema_validator("rocoto", "$defs", "dependency")
        assert not errors(config)
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
    def test_rocoto__RocotoXML__add_task_dependency_datadep(self, instance, root, value):
        age = "00:00:02:00"
        minsize = "1K"
        config = {"datadep": {"attrs": {"age": age, "minsize": minsize}, "value": value}}
        errors = schema_validator("rocoto", "$defs", "dependency")
        assert not errors(config)
        instance._add_task_dependency(e=root, config=config)
        dependency = root[0]
        assert dependency.tag == "dependency"
        child = dependency[0]
        assert child.tag == "datadep"
        assert child.get("age") == age
        assert child.get("minsize") == minsize
        assert child.text == value if isinstance(value, str) else value["cyclestr"]["value"]

    def test_rocoto__RocotoXML__add_task_dependency__fail(self, instance, root):
        config = {"unrecognized": "whatever"}
        with raises(UWConfigError):
            instance._add_task_dependency(e=root, config=config)

    def test_rocoto__RocotoXML__add_task_dependency__fail_bad_operand(self, instance, root):
        config = {"and": {"unrecognized": "whatever"}}
        with raises(UWConfigError):
            instance._add_task_dependency(e=root, config=config)

    def test_rocoto__RocotoXML__add_task_dependency_metataskdep(self, instance, root):
        config = {"metataskdep": {"attrs": {"metatask": "foo"}}}
        errors = schema_validator("rocoto", "$defs", "dependency")
        assert not errors(config)
        instance._add_task_dependency(e=root, config=config)
        dependency = root[0]
        assert dependency.tag == "dependency"
        child = dependency[0]
        assert child.tag == "metataskdep"
        assert child.get("metatask") == "foo"

    @mark.parametrize(
        "tag_config",
        [("and", {"strneq": {"left": "&RUN_GSI;", "right": "YES"}})],
    )
    def test_rocoto__RocotoXML__add_task_dependency__operator(self, instance, root, tag_config):
        tag, config = tag_config
        errors = schema_validator("rocoto", "$defs", "dependency")
        assert not errors(config)
        instance._add_task_dependency_child(e=root, config=config, tag=tag)
        for tag in config:
            assert tag == next(iter(config))

    def test_rocoto__RocotoXML__add_task_dependency__operator_datadep_operand(self, instance, root):
        value = "/some/file"
        config = {"value": value}
        errors = schema_validator("rocoto", "$defs", "dependency")
        assert not errors({"datadep": config})
        instance._add_task_dependency_child(e=root, config=config, tag="datadep")
        e = root[0]
        assert e.tag == "datadep"
        assert e.text == value

    def test_rocoto__RocotoXML__add_task_dependency__operator_task_operand(self, instance, root):
        taskname = "some-task"
        config = {"attrs": {"task": taskname}}
        errors = schema_validator("rocoto", "$defs", "dependency")
        assert not errors({"taskdep": config})
        instance._add_task_dependency_child(e=root, config=config, tag="taskdep")
        e = root[0]
        assert e.tag == "taskdep"
        assert e.get("task") == taskname

    def test_rocoto__RocotoXML__add_task__dependency__operator_timedep_operand(
        self, instance, root
    ):
        value = 20230103120000
        config = value
        errors = schema_validator("rocoto", "$defs", "compoundTimeString")
        assert not errors(config)
        instance._add_task_dependency_child(e=root, config=config, tag="timedep")
        e = root[0]
        assert e.tag == "timedep"
        assert e.text == str(value)

    def test_rocoto__RocotoXML__add_task__dependency_sh__no_attrs(self, instance, root):
        config = {"sh_foo": {"command": "ls"}}
        errors = schema_validator("rocoto", "$defs", "dependency")
        assert not errors(config)
        instance._add_task_dependency(e=root, config=config)
        dependency = root[0]
        assert dependency.tag == "dependency"
        sh = dependency[0]
        assert sh.tag == "sh"
        assert sh.get("name") == "foo"
        assert sh.text == "ls"

    def test_rocoto__RocotoXML__add_task_dependency_sh__with_attrs(self, instance, root):
        config = {"sh_foo": {"attrs": {"runopt": "-c", "shell": "/bin/bash"}, "command": "ls"}}
        errors = schema_validator("rocoto", "$defs", "dependency")
        assert not errors(config)
        instance._add_task_dependency(e=root, config=config)
        dependency = root[0]
        assert dependency.tag == "dependency"
        sh = dependency[0]
        assert sh.tag == "sh"
        assert sh.get("name") == "foo"
        assert sh.get("runopt") == "-c"
        assert sh.get("shell") == "/bin/bash"
        assert sh.text == "ls"

    def test_rocoto__RocotoXML__add_task_dependency__streq(self, instance, root):
        config = {"streq": {"left": "&RUN_GSI;", "right": "YES"}}
        errors = schema_validator("rocoto", "$defs", "dependency")
        assert not errors(config)
        instance._add_task_dependency(e=root, config=config)
        dependency = root[0]
        assert dependency.tag == "dependency"
        streq = dependency[0]
        assert streq.tag == "streq"
        assert streq[0].text == "&RUN_GSI;"
        assert streq[1].text == "YES"

    @mark.parametrize(
        "config",
        [
            ("streq", {"left": "&RUN_GSI;", "right": "YES"}),
            ("strneq", {"left": "&RUN_GSI;", "right": "YES"}),
        ],
    )
    def test_rocoto__RocotoXML__add_task_dependency_strequality(self, config, instance, root):
        errors = schema_validator("rocoto", "$defs", "dependency")
        tag, config = config
        assert not errors({tag: config})
        instance._add_task_dependency_strequality(e=root, config=config, tag=tag)
        element = root[0]
        assert tag == element.tag
        for idx, val in enumerate(config.values()):
            assert element[idx].text == val

    def test_rocoto__RocotoXML__add_task_dependency_taskdep(self, instance, root):
        config = {"taskdep": {"attrs": {"task": "foo"}}}
        errors = schema_validator("rocoto", "$defs", "dependency")
        assert not errors(config)
        instance._add_task_dependency(e=root, config=config)
        dependency = root[0]
        assert dependency.tag == "dependency"
        child = dependency[0]
        assert child.tag == "taskdep"
        assert child.get("task") == "foo"

    def test_rocoto__RocotoXML__add_task_dependency_taskvalid(self, instance, root):
        config = {"taskvalid": {"attrs": {"task": "foo"}}}
        errors = schema_validator("rocoto", "$defs", "dependency")
        assert not errors(config)
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
    def test_rocoto__RocotoXML__add_task_dependency_timedep(self, instance, root, value):
        config = {"timedep": value}
        errors = schema_validator("rocoto", "$defs", "dependency")
        assert not errors(config)
        instance._add_task_dependency(e=root, config=config)
        dependency = root[0]
        assert dependency.tag == "dependency"
        child = dependency[0]
        assert child.tag == "timedep"
        if isinstance(value, dict):
            assert child.xpath("cyclestr")[0].text == value["cyclestr"]["value"]
        else:
            assert child.text == str(value)

    def test_rocoto__RocotoXML__add_task_envar(self, instance, root):
        instance._add_task_envar(root, "foo", "bar")
        envar = root[0]
        name, value = envar
        assert name.tag == "name"
        assert name.text == "foo"
        assert value.tag == "value"
        assert value.text == "bar"

    def test_rocoto__RocotoXML__add_task_envar__compound(self, instance, root):
        instance._add_task_envar(root, "foo", {"cyclestr": {"value": "bar_@Y"}})
        envar = root[0]
        name, value = envar
        child = value[0]
        assert name.tag == "name"
        assert name.text == "foo"
        assert value.tag == "value"
        assert value.text is None
        assert child.text == "bar_@Y"

    def test_rocoto__RocotoXML__add_workflow(self, instance):
        config = {
            "workflow": {
                "attrs": {"realtime": True, "scheduler": "slurm"},
                "cycledef": [],
                "log": {"attrs": {"verbosity": 10}, "value": "1"},
                "tasks": {
                    "task_foo": {
                        "command": "echo hello",
                        "cores": 1,
                        "walltime": "00:01:00",
                    },
                },
            }
        }
        errors = schema_validator("rocoto")
        assert not errors(config)
        with patch.multiple(
            instance, _add_workflow_cycledef=D, _add_workflow_log=D, _add_workflow_tasks=D
        ) as mocks:
            instance._add_workflow(config=config)
        workflow = instance._root
        assert workflow.tag == "workflow"
        assert workflow.get("realtime") == "True"
        assert workflow.get("scheduler") == "slurm"
        mocks["_add_workflow_cycledef"].assert_called_once_with(workflow, [])
        mocks["_add_workflow_log"].assert_called_once_with(workflow, config["workflow"])
        mocks["_add_workflow_tasks"].assert_called_once_with(workflow, config["workflow"]["tasks"])

    def test_rocoto__RocotoXML__add_workflow_cycledef(self, instance, root):
        config: list[dict] = [
            {"attrs": {"group": "g1"}, "spec": "t1"},
            {"attrs": {"group": "g2"}, "spec": "t2"},
        ]
        errors = schema_validator("rocoto", "$defs")
        assert not errors({"cycledef": config})
        instance._add_workflow_cycledef(e=root, config=config)
        for i, item in enumerate(config):
            assert root[i].get("group") == item["attrs"]["group"]
            assert root[i].tag == "cycledef"
            assert root[i].text == item["spec"]

    def test_rocoto__RocotoXML__add_workflow_log__basic(self, instance, root):
        val = "/path/to/logfile"
        instance._add_workflow_log(e=root, config={"log": {"value": val}})
        log = root[0]
        assert log.tag == "log"
        assert log.text == val

    def test_rocoto__RocotoXML__add_workflow_log__cyclestr(self, instance, root):
        val = "/path/to/logfile-@Y@m@d@H"
        instance._add_workflow_log(e=root, config={"log": {"value": {"cyclestr": {"value": val}}}})
        log = root[0]
        assert log.tag == "log"
        assert log.xpath("cyclestr")[0].text == val

    def test_rocoto__RocotoXML__add_workflow_log__verbosity(self, instance, root):
        val = "10"
        config = {"log": {"attrs": {"verbosity": 10}, "value": {"cyclestr": {"value": val}}}}
        instance._add_workflow_log(e=root, config=config)
        log = root[0]
        assert log.attrib["verbosity"] == "10"

    def test_rocoto__RocotoXML__add_workflow_tasks(self, instance, root):
        config = {"metatask_foo": "1", "task_bar": "2"}
        with patch.multiple(instance, _add_metatask=D, _add_task=D) as mocks:
            instance._add_workflow_tasks(e=root, config=config)
        mocks["_add_metatask"].assert_called_once_with(root, "1", "foo")
        mocks["_add_task"].assert_called_once_with(root, "2", "bar")

    def test_rocoto__RocotoXML__config_validate__config(self, assets, instance):
        cfgfile, _ = assets
        instance._config_validate(config=YAMLConfig(cfgfile))

    def test_rocoto__RocotoXML__config_validate_file(self, assets, instance):
        cfgfile, _ = assets
        instance._config_validate(config=cfgfile)

    def test_rocoto__RocotoXML__config_validate__config_fail(self, instance, tmp_path):
        cfgfile = tmp_path / "bad.yaml"
        cfgfile.write_text("not: ok")
        with raises(UWConfigError):
            instance._config_validate(config=YAMLConfig(cfgfile))

    def test_rocoto__RocotoXML__config_validate__file_fail(self, instance, tmp_path):
        cfgfile = tmp_path / "bad.yaml"
        cfgfile.write_text("not: ok")
        with raises(UWConfigError):
            instance._config_validate(config=cfgfile)

    def test_rocoto__RocotoXML__doctype__entities(self, instance):
        assert '<!ENTITY ACCOUNT "myaccount">' in instance._doctype
        assert '<!ENTITY FOO "test.log">' in instance._doctype

    def test_rocoto__RocotoXML__doctype__entities_none(self, instance):
        del instance._config["workflow"]["entities"]
        assert instance._doctype is None

    def test_rocoto__RocotoXML__insert_doctype(self, instance):
        with patch.object(rocoto._RocotoXML, "_doctype", new_callable=PropertyMock) as _doctype:
            _doctype.return_value = "bar"
            assert instance._insert_doctype("foo\nbaz\n") == "foo\nbar\nbaz\n"

    def test_rocoto__RocotoXML__insert_doctype__none(self, instance):
        with patch.object(rocoto._RocotoXML, "_doctype", new_callable=PropertyMock) as _doctype:
            _doctype.return_value = None
            assert instance._insert_doctype("foo\nbaz\n") == "foo\nbaz\n"

    def test_rocoto__RocotoXML__set_and_render_jobname(self, instance):
        config = {"join": "{{jobname}}.log"}
        cfg = instance._set_and_render_jobname(config, "foo")
        assert cfg["join"] == "foo.log"
        assert cfg["jobname"] == "foo"

    def test_rocoto__RocotoXML__set_attrs(self, instance, root):
        config = {"attrs": {"foo": "1", "bar": "2"}}
        instance._set_attrs(e=root, config=config)
        assert root.get("foo") == "1"
        assert root.get("bar") == "2"

    def test_rocoto__RocotoXML__tag_name(self, instance):
        assert instance._tag_name("foo") == ("foo", "")
        assert instance._tag_name("foo_bar") == ("foo", "bar")
        assert instance._tag_name("foo_bar_baz") == ("foo", "bar_baz")
