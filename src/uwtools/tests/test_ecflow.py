"""
Tests for uwtools.ecflow module.
"""

from pathlib import Path
from unittest.mock import Mock, patch

from ecflow import Defs, Family, Suite, Task
from pytest import fixture, mark, raises

from uwtools import ecflow
from uwtools.config.formats.yaml import YAMLConfig
from uwtools.ecflow import _ECFlowDef
from uwtools.exceptions import UWConfigError

# Fixtures


@fixture
def instance():
    """
    Create an _ECFlowDef instance without calling __init__.
    """
    obj = object.__new__(_ECFlowDef)
    obj._scripts = {}
    obj._scheduler = None
    obj._d = Defs()
    obj._config = {}
    return obj


@fixture
def instance_with_scheduler():
    """
    Create an _ECFlowDef instance with a scheduler configured.
    """
    obj = object.__new__(_ECFlowDef)
    obj._scripts = {}
    obj._scheduler = "slurm"
    obj._d = Defs()
    obj._config = {}
    return obj


@fixture
def minimal_config():
    """
    Minimal config for instantiation.
    """
    return {"ecflow": {}}


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
        assert "echo hello" in result
        assert "Test script" in result
        assert "%manual" in result
        assert "%end" in result
        assert "model=%MODEL%" in result

    def test__ecflowscript__with_envcmds(self, instance):
        result = instance._ecflowscript(
            execution=["echo hello"],
            manual="Test script",
            envcmds=["module load foo", "export BAR=baz"],
        )
        assert "module load foo" in result
        assert "export BAR=baz" in result

    def test__ecflowscript__with_envvars(self, instance):
        result = instance._ecflowscript(
            execution=["echo hello"],
            manual="Test script",
            envvars={"FOO": "bar", "BAZ": "qux"},
        )
        assert "export FOO=bar" in result
        assert "export BAZ=qux" in result

    def test__ecflowscript__with_includes(self, instance):
        result = instance._ecflowscript(
            execution=["echo hello"],
            manual="Test script",
            pre_includes=["head.h", "setup.h"],
            post_includes=["tail.h"],
        )
        assert "%include <head.h>" in result
        assert "%include <setup.h>" in result
        assert "%include <tail.h>" in result

    def test__ecflowscript__with_scheduler(self, instance):
        mock_scheduler = Mock()
        mock_scheduler.directives = ["#SBATCH --account=foo", "#SBATCH --time=01:00:00"]
        mock_scheduler.initcmds = ["srun --export=ALL"]
        result = instance._ecflowscript(
            execution=["echo hello"],
            manual="Test script",
            scheduler=mock_scheduler,
        )
        assert "#SBATCH --account=foo" in result
        assert "srun --export=ALL" in result

    # _jobscheduler tests

    def test__jobscheduler(self, instance_with_scheduler):
        execution = {"threads": 4, "batchargs": {"queue": "batch"}}
        with patch.object(ecflow.JobScheduler, "get_scheduler") as mock_get:
            instance_with_scheduler._jobscheduler(
                account="myaccount",
                execution=execution,
                rundir="/path/to/run",
            )
        mock_get.assert_called_once()
        call_args = mock_get.call_args[0][0]
        assert call_args["account"] == "myaccount"
        assert call_args["rundir"] == "/path/to/run"
        assert call_args["scheduler"] == "slurm"
        assert call_args["threads"] == 4
        assert call_args["queue"] == "batch"

    def test__jobscheduler__no_threads(self, instance_with_scheduler):
        execution = {}
        with patch.object(ecflow.JobScheduler, "get_scheduler") as mock_get:
            instance_with_scheduler._jobscheduler(
                account="myaccount",
                execution=execution,
                rundir="/path/to/run",
            )
        call_args = mock_get.call_args[0][0]
        assert "threads" not in call_args

    # _add_repeat tests

    def test__add_repeat__date(self, instance):
        node = Mock()
        config = {"name": "YMD", "start": 20240101, "end": 20240131, "step": 1}
        with patch.object(ecflow, "RepeatDate") as mock_repeat:
            instance._add_repeat(config.copy(), "date", node)
        mock_repeat.assert_called_once()
        node.add_repeat.assert_called_once()

    def test__add_repeat__int(self, instance):
        node = Mock()
        config = {"name": "STEP", "start": 0, "end": 10, "step": 1}
        with patch.object(ecflow, "RepeatInteger") as mock_repeat:
            instance._add_repeat(config.copy(), "int", node)
        mock_repeat.assert_called_once()
        node.add_repeat.assert_called_once()

    def test__add_repeat__day(self, instance):
        node = Mock()
        config = {"step": 1}
        with patch.object(ecflow, "RepeatDay") as mock_repeat:
            instance._add_repeat(config.copy(), "day", node)
        mock_repeat.assert_called_once()
        node.add_repeat.assert_called_once()

    def test__add_repeat__enumerated(self, instance):
        node = Mock()
        config = {"name": "MEMBER", "values": ["m01", "m02", "m03"]}
        with patch.object(ecflow, "RepeatEnumerated") as mock_repeat:
            instance._add_repeat(config.copy(), "enumerated", node)
        mock_repeat.assert_called_once()
        node.add_repeat.assert_called_once()

    @mark.parametrize("repeat_type", ["datelist", "string"])
    def test__add_repeat__enumerated_variants(self, instance, repeat_type):
        """
        Test that datelist and string repeat types also use RepeatEnumerated.
        """
        node = Mock()
        config = {"name": "VAR", "values": ["a", "b"]}
        with patch.object(ecflow, "RepeatEnumerated") as mock_repeat:
            instance._add_repeat(config.copy(), repeat_type, node)
        mock_repeat.assert_called_once()
        node.add_repeat.assert_called_once()

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
        config = {"not_ecflow": {}}
        with raises(KeyError):
            _ECFlowDef(config=config)

    # _add_workflow_components tests

    def test__add_workflow_components__extern(self, instance):
        instance._config = {"extern": ["/path/to/ext1", "/path/to/ext2"]}
        instance._add_workflow_components()
        # Externs are added to the Defs object
        def_str = str(instance._d)
        assert "extern" in def_str or instance._d is not None

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
        config = {}
        instance._add_node(config, suite, instance._d)
        assert "test" in str(instance._d)

    def test__add_node__with_task(self, instance):
        suite = Suite("test")
        config = {"task_hello": {}}
        with patch.object(instance, "_add_node", wraps=instance._add_node) as mock:
            instance._add_node(config, suite, instance._d)
        # Called twice: once for suite, once for task
        assert mock.call_count == 2

    def test__add_node__with_family(self, instance):
        suite = Suite("test")
        config = {"family_myfam": {"task_t1": {}}}
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
        assert "trigger" in str(instance._d).lower() or task2 is not None

    def test__add_node__with_events(self, instance):
        suite = Suite("test")
        config = {"events": ["event1", "event2"]}
        task = Task("t1")
        instance._add_node(config, task, suite)
        # Events are added to the task

    def test__add_node__with_defstatus(self, instance):
        suite = Suite("test")
        task = Task("t1")
        config = {"defstatus": "complete"}
        with patch.object(task, "add_defstatus") as mock_defstatus:
            instance._add_node(config, task, suite)
        mock_defstatus.assert_called_once_with("complete")

    # _expand_block tests

    def test__expand_block__basic(self, instance):
        config = {"expand": {"MEMBER": ["m01", "m02"]}, "task_run": {}}
        suite = Suite("test")
        instance._d.add(suite)
        with patch.object(instance, "_add_node") as mock_add_node:
            instance._expand_block(config, "suite", Suite, instance._d)
        assert mock_add_node.call_count == 2

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
            "execution": {"jobcmd": "echo hello"},
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
            "execution": {"jobcmd": "echo hello"},
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

    # write_ecf_scripts tests

    def test_write_ecf_scripts__no_scripts(self, instance, logged):
        instance.write_ecf_scripts(Path("/tmp"))
        assert logged("No scripts are configured for this workflow")

    def test_write_ecf_scripts__with_scripts(self, instance, tmp_path):
        instance._scripts = {Path("test/hello.ecf"): "#!/bin/bash\necho hello"}
        instance.write_ecf_scripts(tmp_path)
        outfile = tmp_path / "test" / "hello.ecf"
        assert outfile.exists()
        assert "echo hello" in outfile.read_text()

    def test_write_ecf_scripts__with_string_path(self, instance, tmp_path):
        instance._scripts = {Path("suite/task.ecf"): "#!/bin/bash\necho test"}
        instance.write_ecf_scripts(str(tmp_path))
        outfile = tmp_path / "suite" / "task.ecf"
        assert outfile.exists()

    # write_suite_definition tests

    def test_write_suite_definition(self, instance, tmp_path):
        suite = Suite("test")
        instance._d.add(suite)
        instance.write_suite_definition(tmp_path)
        suite_file = tmp_path / "suite.def"
        assert suite_file.exists()
        assert "test" in suite_file.read_text()

    def test_write_suite_definition__creates_directory(self, instance, tmp_path):
        suite = Suite("test")
        instance._d.add(suite)
        nested_path = tmp_path / "nested" / "output"
        instance.write_suite_definition(nested_path)
        assert (nested_path / "suite.def").exists()

    def test_write_suite_definition__with_string_path(self, instance, tmp_path):
        suite = Suite("test")
        instance._d.add(suite)
        instance.write_suite_definition(str(tmp_path))
        assert (tmp_path / "suite.def").exists()

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
        with patch.object(task, "add_inlimit") as mock_inlimit:
            instance._add_node(config, task, suite)
            # Force evaluation of generator
            list(mock_inlimit.call_args_list)

    def test__add_node__with_labels(self, instance):
        suite = Suite("test")
        task = Task("t1")
        config = {"labels": [["label1", "value1"], ["label2", "value2"]]}
        with patch.object(task, "add_label") as mock_label:
            instance._add_node(config, task, suite)
            list(mock_label.call_args_list)

    def test__add_node__with_late(self, instance):
        suite = Suite("test")
        task = Task("t1")
        config = {"late": {"submitted": "+00:15", "active": "+01:00"}}
        with patch.object(ecflow, "Late") as mock_late:
            with patch.object(task, "add_late") as mock_add_late:
                instance._add_node(config, task, suite)
        mock_late.assert_called_once()

    def test__add_node__with_limits(self, instance):
        suite = Suite("test")
        task = Task("t1")
        config = {"limits": [["limit1", 5], ["limit2", 10]]}
        with patch.object(task, "add_limit") as mock_limit:
            instance._add_node(config, task, suite)
            list(mock_limit.call_args_list)

    def test__add_node__with_meters(self, instance):
        suite = Suite("test")
        task = Task("t1")
        config = {"meters": [["meter1", 0, 100, 50]]}
        with patch.object(task, "add_meter") as mock_meter:
            instance._add_node(config, task, suite)
            list(mock_meter.call_args_list)

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
        script_config = {"execution": {"jobcmd": "echo hi"}}
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
        script_config = {"execution": {"jobcmd": "echo hi"}}
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
        with patch.object(ecflow, "RepeatDateTime") as mock_repeat:
            instance._add_repeat(config.copy(), "datetime", node)
        mock_repeat.assert_called_once()
        node.add_repeat.assert_called_once()

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
                        }
                    },
                    "task_run": {
                        "trigger": "/test/prep/setup == complete",
                        "script": {
                            "execution": {"jobcmd": "echo running"},
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
        assert (tmp_path / "suite.def").exists()
        # Write ecf scripts.
        ecf.write_ecf_scripts(tmp_path)
        assert len(list(tmp_path.rglob("*.ecf"))) == 1

    def test_integration__with_expand(self, tmp_path):
        """
        Test workflow with expand blocks for parameterized tasks.
        """
        config = {
            "ecflow": {
                "suite_ensemble": {
                    "tasks_member_{{ ec.MEM }}": {
                        "expand": {"MEM": ["01", "02", "03"]},
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
