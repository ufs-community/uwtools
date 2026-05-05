"""
Tests for uwtools.ecflow module.
"""

import sys
from io import StringIO
from pathlib import Path
from unittest.mock import Mock, call, patch

import yaml
from ecflow import Defs, DState, Suite, Task  # type: ignore[import-untyped]
from pytest import fixture, mark, raises

from uwtools import ecflow
from uwtools.config.formats.yaml import YAMLConfig
from uwtools.ecflow import _ECFlowDef
from uwtools.exceptions import UWConfigError
from uwtools.utils.file import _stdinproxy

# Fixtures


@fixture
def assets(tmp_path, minimal_config):
    yaml_file = tmp_path / "config.yaml"
    YAMLConfig(minimal_config).dump(yaml_file)
    script_path = tmp_path / "scripts"
    script_path.mkdir(exist_ok=True, parents=True)
    expected = "#5.15.2\n# enddef\n"
    return yaml_file, script_path, expected


@fixture
def instance(minimal_config):
    """
    Create a minimal _ECFlowDef instance.
    """
    return _ECFlowDef(minimal_config)


@fixture
def instance_with_scheduler(instance):
    """
    Create an _ECFlowDef instance with a scheduler configured.
    """
    instance._scheduler = "slurm"
    return instance


@fixture
def minimal_config():
    """
    Minimal config for instantiation.
    """
    return {"ecflow": {}}


def assert_line_in(result: str, line: str) -> None:
    """
    Assert that a line exists in result, ignoring surrounding whitespace.
    """
    assert line in (x.strip() for x in result.splitlines())


def assert_lines_in_order(result: str, expected: list[str]) -> None:
    """
    Assert that expected lines are present in result in the same relative order.
    """
    lines = [x.strip() for x in result.splitlines()]
    actual = [line for line in lines if line in expected]
    assert actual == expected


# Tests


class TestECFlowDef:
    """
    Tests for class uwtools.ecflow._ECFlowDef.
    """

    # _tag_name tests

    @mark.parametrize(
        ("key", "expected"),
        [
            ("task_foo", ("task", "foo")),
            ("family_my_family", ("family", "my_family")),
            ("suite_prod", ("suite", "prod")),
            ("vars", ("vars", "")),
            ("task_foo_bar_baz", ("task", "foo_bar_baz")),
        ],
    )
    def test__tag_name(self, instance, key, expected):
        assert instance._tag_name(key) == expected

    # _ecflowscript tests

    def test__ecflowscript__minimal(self, instance):
        result = instance._ecflowscript(
            execution=["echo hello"],
            manual="Test script",
        )
        assert_line_in(result, "echo hello")
        assert_line_in(result, "Test script")
        assert_line_in(result, "%manual")
        assert_line_in(result, "%end")
        assert_line_in(result, "model=%MODEL%")

    def test__ecflowscript__with_envcmds(self, instance):
        result = instance._ecflowscript(
            execution=["echo hello"],
            manual="Test script",
            envcmds=["module load foo", "export BAR=baz"],
        )
        assert_line_in(result, "module load foo")
        assert_line_in(result, "export BAR=baz")

    def test__ecflowscript__with_envvars(self, instance):
        result = instance._ecflowscript(
            execution=["echo hello"],
            manual="Test script",
            envvars={"FOO": "bar", "BAZ": "qux"},
        )
        assert_line_in(result, "export FOO=bar")
        assert_line_in(result, "export BAZ=qux")

    def test__ecflowscript__with_includes(self, instance):
        result = instance._ecflowscript(
            execution=["echo hello"],
            manual="Test script",
            pre_includes=["head.h", "setup.h"],
            post_includes=["tail.h"],
        )
        assert_lines_in_order(
            result,
            ["%include <head.h>", "%include <setup.h>", "%include <tail.h>"],
        )

    def test__ecflowscript__with_scheduler(self, instance):
        mock_scheduler = Mock()
        mock_scheduler.directives = ["#SBATCH --account=foo", "#SBATCH --time=01:00:00"]
        mock_scheduler.initcmds = ["srun --export=ALL"]
        result = instance._ecflowscript(
            execution=["echo hello"],
            manual="Test script",
            scheduler=mock_scheduler,
        )
        assert_line_in(result, "#SBATCH --account=foo")
        assert_line_in(result, "srun --export=ALL")

    # _jobscheduler tests

    def test__jobscheduler(self, instance_with_scheduler):
        execution = {"threads": 4, "batchargs": {"queue": "batch"}}
        with patch.object(ecflow.JobScheduler, "get_scheduler") as get_scheduler:
            instance_with_scheduler._jobscheduler(
                account="myaccount",
                execution=execution,
                rundir="/path/to/run",
            )
        get_scheduler.assert_called_once_with(
            {
                "account": "myaccount",
                "rundir": "/path/to/run",
                "scheduler": "slurm",
                "stdout": "/path/to/run.out",
                "threads": 4,
                "queue": "batch",
            }
        )

    def test__jobscheduler__no_threads(self, instance_with_scheduler):
        execution: dict = {}
        with patch.object(ecflow.JobScheduler, "get_scheduler") as get_scheduler:
            instance_with_scheduler._jobscheduler(
                account="myaccount",
                execution=execution,
                rundir="/path/to/run",
            )
        get_scheduler.assert_called_once_with(
            {
                "account": "myaccount",
                "rundir": "/path/to/run",
                "scheduler": "slurm",
                "stdout": "/path/to/run.out",
            }
        )

    # _add_repeat tests

    def test__add_repeat__date(self, instance):
        node = Mock()
        common = {"name": "YMD", "start": 20240101, "end": 20240131}
        with patch.object(ecflow, "RepeatDate") as repeat_date:
            instance._add_repeat({**common, "step": 1}, "date", node)
        repeat_date.assert_called_once_with(**{**common, "delta": 1})
        node.add_repeat.assert_called_once_with(repeat_date.return_value)

    def test__add_repeat__int(self, instance):
        node = Mock()
        config = {"name": "STEP", "start": 0, "end": 10, "step": 1}
        with patch.object(ecflow, "RepeatInteger") as repeat_integer:
            instance._add_repeat(config.copy(), "int", node)
        repeat_integer.assert_called_once_with(**config)
        node.add_repeat.assert_called_once_with(repeat_integer.return_value)

    def test__add_repeat__day(self, instance):
        node = Mock()
        config = {"step": 1}
        with patch.object(ecflow, "RepeatDay") as repeat_day:
            instance._add_repeat(config.copy(), "day", node)
        repeat_day.assert_called_once_with(**config)
        node.add_repeat.assert_called_once_with(repeat_day.return_value)

    def test__add_repeat__enumerated(self, instance):
        node = Mock()
        config = {"name": "MEMBER", "values": ["m01", "m02", "m03"]}
        with patch.object(ecflow, "RepeatEnumerated") as repeat_enumerated:
            instance._add_repeat(config.copy(), "enumerated", node)
        repeat_enumerated.assert_called_once_with(**config)
        node.add_repeat.assert_called_once_with(repeat_enumerated.return_value)

    @mark.parametrize("repeat_type", ["datelist", "string"])
    def test__add_repeat__enumerated_variants(self, instance, repeat_type):
        """
        Test that datelist and string repeat types also use RepeatEnumerated.
        """
        node = Mock()
        config = {"name": "VAR", "values": ["a", "b"]}
        with patch.object(ecflow, "RepeatEnumerated") as repeat_enumerated:
            instance._add_repeat(config.copy(), repeat_type, node)
        repeat_enumerated.assert_called_once_with(**config)
        node.add_repeat.assert_called_once_with(repeat_enumerated.return_value)

    # __str__ tests

    def test__str__(self, instance):
        result = str(instance)
        assert isinstance(result, str)

    # __init__ tests

    def test__init__with_dict(self, minimal_config):
        ecf = _ECFlowDef(config=minimal_config)
        assert ecf._config == {}
        assert ecf._scheduler is None
        assert isinstance(ecf._d, Defs)

    def test__init__with_scheduler(self):
        config = {"ecflow": {"scheduler": "slurm"}}
        ecf = _ECFlowDef(config=config)
        assert ecf._scheduler == "slurm"

    def test__init__with_path(self, tmp_path):
        config_file = tmp_path / "config.yaml"
        config_file.write_text("ecflow:\n  scheduler: pbs\n")
        ecf = _ECFlowDef(config=config_file)
        assert ecf._scheduler == "pbs"
        assert isinstance(ecf._d, Defs)

    def test__init__with_config_object(self, minimal_config):
        cfg = YAMLConfig(minimal_config)
        ecf = _ECFlowDef(config=cfg)
        assert ecf._config == {}
        assert isinstance(ecf._d, Defs)

    def test__init__missing_ecflow_key(self):
        config: dict = {"not_ecflow": {}}
        with raises(UWConfigError):
            _ECFlowDef(config=config)

    # _add_workflow_components tests

    def test__add_workflow_components__extern(self, instance):
        instance._config = {"extern": ["/path/to/ext1", "/path/to/ext2"]}
        instance._add_workflow_components()
        # Externs are added to the Defs object
        def_str = str(instance._d)
        assert "/path/to/ext1" in def_str
        assert "/path/to/ext2" in def_str

    def test__add_workflow_components__vars(self, instance):
        instance._config = {"vars": {"FOO": "bar"}}
        with patch.object(instance._d, "add_variable") as mock_add_var:
            instance._add_workflow_components()
        mock_add_var.assert_called_once_with({"FOO": "bar"})

    def test__add_workflow_components__suite(self, instance):
        instance._config = {"suite_test": {}}
        with patch.object(instance, "_add_node") as mock_add_node:
            instance._add_workflow_components()
        mock_add_node.assert_called_once()

    # _add_node tests

    def test__add_node__basic(self, instance):
        suite = Suite("test")
        config: dict = {}
        instance._add_node(config, suite, instance._d)
        assert "test" in str(instance._d)

    def test__add_node__with_task(self, instance):
        suite = Suite("test")
        config: dict = {"task_hello": {}}
        with patch.object(instance, "_add_node", wraps=instance._add_node) as mock:
            instance._add_node(config, suite, instance._d)
        # Called twice: once for suite, once for task
        assert mock.call_count == 2

    def test__add_node__with_family(self, instance):
        suite = Suite("test")
        config: dict = {"family_myfam": {"task_t1": {}}}
        with patch.object(instance, "_add_node", wraps=instance._add_node) as mock:
            instance._add_node(config, suite, instance._d)
        # Called for suite, family, and task
        assert mock.call_count == 3

    def test__add_node__with_vars(self, instance):
        suite = Suite("test")
        config = {"vars": {"VAR1": "value1"}}
        instance._add_node(config, suite, instance._d)
        assert "VAR1" in str(instance._d)

    def test__add_node__with_trigger(self, instance):
        suite = Suite("test")
        task = Task("t1")
        suite.add(task)
        config = {"trigger": "t1 == complete"}
        task2 = Task("t2")
        instance._add_node(config, task2, suite)
        assert str(task2.get_trigger()) == "t1 == complete"

    def test__add_node__with_events(self, instance):
        suite = Suite("test")
        config = {"events": ["event1", "event2"]}
        task = Task("t1")
        instance._add_node(config, task, suite)
        assert task.find_event("event1") is not None
        assert task.find_event("event2") is not None
        assert [event.name() for event in task.events] == ["event1", "event2"]

    def test__add_node__with_events_multiarg(self, instance):
        suite = Suite("test")
        config = {"events": [[1, "event1"], [2, "event2"]]}
        task = Task("t1")
        instance._add_node(config, task, suite)
        assert task.find_event("event1") is not None
        assert task.find_event("event2") is not None
        assert [event.name() for event in task.events] == ["event1", "event2"]

    def test__add_node__with_defstatus(self, instance):
        suite = Suite("test")
        task = Task("t1")
        config = {"defstatus": "complete"}
        instance._add_node(config, task, suite)
        assert task.get_defstatus() == DState.complete

    # _expand_block tests

    def test__expand_block__basic(self, instance):
        config = {"expand": {"MEMBER": ["m01", "m02"]}, "task_{{ ec.MEMBER }}": {}}
        suite = Suite("test")
        instance._d.add(suite)
        with patch.object(instance, "_add_node") as mock_add_node:
            instance._expand_block(config, "{{ ec.MEMBER }}", Task, suite)
        assert mock_add_node.call_count == 2
        assert [x.kwargs["node"].name() for x in mock_add_node.call_args_list] == ["m01", "m02"]

    def test__expand_block__mismatched_lengths(self, instance):
        config = {
            "expand": {"VAR1": ["a", "b"], "VAR2": ["x", "y", "z"]},  # Different lengths
        }
        suite = Suite("test")
        instance._d.add(suite)
        with raises(UWConfigError, match="same length"):
            instance._expand_block(config, "suite", Suite, suite)

    # _create_ecf_script tests

    def test__create_ecf_script(self, instance):
        task = Task("hello")
        suite = Suite("test")
        suite.add(task)
        instance._d.add(suite)
        config = {
            "execution": {"incantation": "echo hello"},
            "manual": "Test task",
        }
        instance._create_ecf_script(config, task)
        assert len(instance._scripts) == 1
        script_content = list(instance._scripts.values())[0]
        assert "echo hello" in script_content

    def test__create_ecf_script__with_scheduler(self, instance_with_scheduler):
        task = Task("hello")
        suite = Suite("test")
        suite.add(task)
        instance_with_scheduler._d.add(suite)
        config = {
            "execution": {"incantation": "echo hello"},
            "account": "myaccount",
            "rundir": "/path/to/run",
        }
        with patch.object(instance_with_scheduler, "_jobscheduler") as mock_js:
            mock_scheduler = Mock()
            mock_scheduler.directives = []
            mock_scheduler.initcmds = []
            mock_js.return_value = mock_scheduler
            instance_with_scheduler._create_ecf_script(config, task)
        mock_js.assert_called_once()

    def test__create_ecf_script__without_incantation(self, instance):
        task = Task("hello")
        suite = Suite("test")
        suite.add(task)
        instance._d.add(suite)
        config = {
            "execution": {},
            "manual": "Test task",
        }

        with raises(UWConfigError, match="must include 'incantation'"):
            instance._create_ecf_script(config, task)

    # write_ecf_scripts tests

    def test_write_ecf_scripts__no_scripts(self, instance, logged, tmp_path):
        instance.write_ecf_scripts(tmp_path)
        assert logged("No scripts are configured for this workflow")

    def test_write_ecf_scripts__with_scripts(self, instance, tmp_path):
        instance._scripts = {Path("test/hello.ecf"): "#!/bin/bash\necho hello"}
        instance.write_ecf_scripts(tmp_path)
        outfile = tmp_path / "test" / "hello.ecf"
        assert outfile.is_file()
        assert "echo hello" in outfile.read_text()

    def test_write_ecf_scripts__with_string_path(self, instance, tmp_path):
        instance._scripts = {Path("suite/task.ecf"): "#!/bin/bash\necho test"}
        instance.write_ecf_scripts(str(tmp_path))
        outfile = tmp_path / "suite" / "task.ecf"
        assert outfile.is_file()

    # write_suite_definition tests

    def test_write_suite_definition(self, instance, tmp_path):
        suite = Suite("test")
        instance._d.add(suite)
        instance.write_suite_definition(tmp_path)
        suite_file = tmp_path / "suite.def"
        assert suite_file.is_file()
        assert "test" in suite_file.read_text()

    def test_write_suite_definition__creates_directory(self, instance, tmp_path):
        suite = Suite("test")
        instance._d.add(suite)
        nested_path = tmp_path / "nested" / "output"
        instance.write_suite_definition(nested_path)
        assert (nested_path / "suite.def").is_file()

    # Additional tests for missing coverage

    def test__add_workflow_components__suites(self, instance):
        instance._config = {"suites_test": {"expand": {"VAR": ["a", "b"]}}}
        with patch.object(instance, "_expand_block") as mock_expand:
            instance._add_workflow_components()
        mock_expand.assert_called_once()

    def test__add_node__with_families(self, instance):
        suite = Suite("test")
        config = {"families_fam": {"expand": {"VAR": ["a", "b"]}}}
        with patch.object(instance, "_expand_block") as mock_expand:
            instance._add_node(config, suite, instance._d)
        mock_expand.assert_called_once()

    def test__add_node__with_tasks(self, instance):
        suite = Suite("test")
        config = {"tasks_t": {"expand": {"VAR": ["a", "b"]}}}
        with patch.object(instance, "_expand_block") as mock_expand:
            instance._add_node(config, suite, instance._d)
        mock_expand.assert_called_once()

    def test__add_node__with_inlimits(self, instance):
        suite = Suite("test")
        task = Task("t1")
        config = {"inlimits": [["limit1", "/path"], ["limit2", "/path2"]]}
        with patch.object(task, "add_inlimit") as add_inlimit:
            instance._add_node(config, task, suite)
        assert add_inlimit.call_args_list == [
            call("limit1", "/path"),
            call("limit2", "/path2"),
        ]

    def test__add_node__with_labels(self, instance):
        suite = Suite("test")
        task = Task("t1")
        config = {"labels": [["label1", "value1"], ["label2", "value2"]]}
        with patch.object(task, "add_label") as add_label:
            instance._add_node(config, task, suite)
        assert add_label.call_args_list == [
            call("label1", "value1"),
            call("label2", "value2"),
        ]

    def test__add_node__with_late(self, instance):
        suite = Suite("test")
        task = Task("t1")
        config = {"late": {"submitted": "+00:15", "active": "+01:00"}}
        with patch.object(ecflow, "Late") as mock_late, patch.object(task, "add_late"):
            instance._add_node(config, task, suite)
        mock_late.assert_called_once()

    def test__add_node__with_limits(self, instance):
        suite = Suite("test")
        task = Task("t1")
        config = {"limits": [["limit1", 5], ["limit2", 10]]}
        with patch.object(task, "add_limit") as add_limit:
            instance._add_node(config, task, suite)
        assert add_limit.call_args_list == [
            call("limit1", 5),
            call("limit2", 10),
        ]

    def test__add_node__with_meters(self, instance):
        suite = Suite("test")
        task = Task("t1")
        config = {"meters": [["meter1", 0, 100, 50]]}
        with patch.object(task, "add_meter") as add_meter:
            instance._add_node(config, task, suite)
        assert add_meter.call_args_list == [
            call("meter1", 0, 100, 50),
        ]

    def test__add_node__with_repeat(self, instance):
        suite = Suite("test")
        task = Task("t1")
        config = {"repeat_int": {"name": "STEP", "start": 0, "end": 10}}
        with patch.object(instance, "_add_repeat") as mock_repeat:
            instance._add_node(config, task, suite)
        mock_repeat.assert_called_once()

    def test__add_node__with_script_then_continue(self, instance):
        """
        Test that loop continues after processing script case (covers branch 196->159).
        """
        suite = Suite("test")
        task = Task("t1")
        # Place script FIRST so loop must continue to process trigger afterward.
        script_config = {"execution": {"incantation": "echo hi"}}
        config = {"script": script_config, "trigger": "1==1"}
        instance._add_node(config, task, suite)
        # Verify script was created and loop continued to process trigger.
        assert len(instance._scripts) == 1
        assert task.get_trigger() is not None

    def test__add_node__with_script_last(self, instance):
        """
        Test that loop exits after processing script as the last item.
        """
        suite = Suite("test")
        task = Task("t1")
        # Place script LAST so loop exits after processing it.
        script_config = {"execution": {"incantation": "echo hi"}}
        config = {"trigger": "1==1", "script": script_config}
        instance._add_node(config, task, suite)
        # Verify both trigger and script were processed.
        assert task.get_trigger() is not None
        assert len(instance._scripts) == 1

    def test__add_node__unrecognized_tag(self, instance):
        """
        Test that unrecognized tags raise AssertionError.
        """
        suite = Suite("test")
        task = Task("t1")
        config = {"unknown_tag": "value"}
        with raises(AssertionError, match="Unrecognized tag: unknown"):
            instance._add_node(config, task, suite)

    def test__add_node__with_expand_tag(self, instance):
        """
        Test that expand tag is silently skipped (already processed by _expand_block).
        """
        suite = Suite("test")
        task = Task("t1")
        config = {"expand": {"VAR": ["a", "b"]}, "trigger": "1==1"}
        instance._add_node(config, task, suite)
        # Expand tag should be skipped, trigger should be processed.
        assert task.get_trigger() is not None

    def test__add_repeat__datetime(self, instance):
        node = Mock()
        config = {
            "name": "DT",
            "start": "20240101T000000",
            "end": "20240101T120000",
            "delta": "01:00:00",
        }
        with patch.object(ecflow, "RepeatDateTime") as repeat_datetime:
            instance._add_repeat(config.copy(), "datetime", node)
        repeat_datetime.assert_called_once_with(**config)
        node.add_repeat.assert_called_once_with(repeat_datetime.return_value)

    def test__add_repeat__unknown_type(self, instance):
        node = Mock()
        config = {"name": "X"}
        with raises(UnboundLocalError):
            instance._add_repeat(config, "unknown", node)

    # Integration tests

    def test_integration__full_workflow(self, tmp_path):
        """
        Test creating a complete workflow from config, writing outputs.
        """
        config = {
            "ecflow": {
                "suite_test": {
                    "vars": {"SUITE_VAR": "value"},
                    "family_prep": {
                        "task_setup": {
                            "trigger": "1==1",
                            "script": {
                                "execution": {
                                    "executable": "prep.exe",
                                    "incantation": "echo running",
                                },
                            },
                        },
                    },
                    "task_run": {
                        "trigger": "/test/prep/setup == complete",
                        "script": {
                            "execution": {"executable": "run.exe", "incantation": "echo running"},
                        },
                    },
                }
            }
        }
        ecf = _ECFlowDef(config=config)
        # Verify suite definition was created.
        suite_def = str(ecf)
        assert "suite test" in suite_def
        assert "family prep" in suite_def
        assert "task setup" in suite_def
        assert "task run" in suite_def
        # Write suite definition.
        ecf.write_suite_definition(tmp_path)
        assert (tmp_path / "suite.def").is_file()
        # Write ecf script.
        ecf.write_ecf_scripts(tmp_path)
        assert (tmp_path / "test" / "run.ecf").is_file()

    def test_integration__with_expand(self):
        """
        Test workflow with expand blocks for parameterized tasks.
        """
        config = {
            "ecflow": {
                "suite_ensemble": {
                    "tasks_member_{{ ec.MEM }}": {
                        "expand": {"MEM": ["01", "02", "03"]},
                        "script": {"execution": {"incantation": "hello"}},
                    }
                }
            }
        }
        ecf = _ECFlowDef(config=config)
        suite_def = str(ecf)
        # All three members should be created.
        assert "task member_01" in suite_def
        assert "task member_02" in suite_def
        assert "task member_03" in suite_def


def test_ecflow_realize__cfg_to_file(tmp_path, assets):
    cfgfile, _, expected = assets
    ecflow.realize(config=YAMLConfig(cfgfile), output_path=tmp_path)
    output = (tmp_path / "suite.def").read_text()
    assert output == expected


def test_ecflow_realize__cfg_to_stdout(capsys, assets):
    cfgfile, _, expected = assets
    ecflow.realize(config=YAMLConfig(cfgfile))
    assert capsys.readouterr().out == expected


def test_ecflow_realize__file_to_file(tmp_path, assets):
    cfgfile, _, expected = assets
    ecflow.realize(config=cfgfile, output_path=tmp_path)
    output = (tmp_path / "suite.def").read_text()
    assert output == expected


def test_ecflow_realize__file_to_stdout(capsys, assets):
    cfgfile, _, expected = assets
    ecflow.realize(config=cfgfile)
    assert capsys.readouterr().out == expected


def test_ecflow_realize__write_scripts(capsys, assets):
    cfgfile, script_path, expected = assets
    with patch.object(ecflow._ECFlowDef, "write_ecf_scripts") as write_scripts:
        ecflow.realize(config=cfgfile, scripts_path=script_path)
        write_scripts.assert_called_once_with(script_path)
    assert capsys.readouterr().out == expected


def test_validate__path(tmp_path, minimal_config):
    path = tmp_path / "config.yaml"
    YAMLConfig(minimal_config).dump(path)
    assert ecflow.validate(path)


def test_validate__dict(minimal_config):
    assert ecflow.validate(minimal_config)


def test_validate__yamlconfig(minimal_config):
    assert ecflow.validate(YAMLConfig(minimal_config))


def test_validate__stdin(minimal_config):
    _stdinproxy.cache_clear()
    with StringIO(yaml.safe_dump(minimal_config)) as sio, patch.object(sys, "stdin", new=sio):
        assert ecflow.validate()


def test_validate__invalid(tmp_path):
    yaml_file = tmp_path / "ecflow.yaml"
    yaml_file.write_text("not_ecflow: {}\n")
    with raises(UWConfigError) as e:
        ecflow.validate(yaml_file)
    assert "YAML validation errors" in str(e.value)
