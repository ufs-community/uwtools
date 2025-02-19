# pylint: disable=missing-function-docstring,protected-access,redefined-outer-name

import datetime as dt
import logging
import os
import sys
from pathlib import Path
from types import SimpleNamespace as ns
from unittest.mock import patch

from iotaa import refs
from pytest import fixture, mark, raises

from uwtools.api import execute
from uwtools.exceptions import UWError
from uwtools.logging import log
from uwtools.tests.support import fixture_path, logged, regex_logged

# Fixtures


@fixture
def args():
    return ns(
        classname="TestDriver",
        config=fixture_path("testdriver.yaml"),
        module=fixture_path("testdriver.py"),
        schema_file=fixture_path("testdriver.jsonschema"),
        task="forty_two",
    )


@fixture
def kwargs(args):
    return dict(
        classname=args.classname,
        config=args.config,
        module=args.module,
        schema_file=args.schema_file,
        task=args.task,
    )


# Tests


@mark.parametrize("key,val", [("batch", True), ("leadtime", 6)])
def test_execute_fail_bad_args(caplog, key, kwargs, val):
    kwargs.update({"cycle": dt.datetime.now(), key: val})
    assert execute.execute(**kwargs) is None
    assert logged(caplog, f"TestDriver does not accept argument '{key}'")


def test_execute_fail_stdin_not_ok(kwargs):
    kwargs["config"] = None
    kwargs["cycle"] = dt.datetime.now()
    kwargs["stdin_ok"] = False
    with raises(UWError) as e:
        execute.execute(**kwargs)
    assert str(e.value) == "Set stdin_ok=True to permit read from stdin"


@mark.parametrize("remove", ([], ["schema_file"]))
def test_execute_pass(caplog, kwargs, remove, tmp_path):
    for kwarg in remove:
        del kwargs[kwarg]
    kwargs["cycle"] = dt.datetime.now()
    log.setLevel(logging.DEBUG)
    graph_file = tmp_path / "g.dot"
    graph_code = "DOT code"
    kwargs["graph_file"] = graph_file
    with patch.object(execute, "graph", return_value=graph_code):
        assert refs(execute.execute(**kwargs)) == 42
    assert regex_logged(caplog, "Instantiated %s with" % kwargs["classname"])
    with open(graph_file, "r", encoding="utf-8") as f:
        assert f.read().strip() == graph_code


def test_execute_fail_cannot_load_driver_class(kwargs):
    kwargs["module"] = "bad_module_name"
    assert execute.execute(**kwargs) is None


def test_tasks_fail(args, caplog, tmp_path):
    module = tmp_path / "not.py"
    tasks = execute.tasks(classname=args.classname, module=module)
    assert tasks == {}
    assert logged(
        caplog, "Could not get tasks from class %s in module %s" % (args.classname, module)
    )


def test_tasks_fail_no_cycle(args, caplog, kwargs):
    log.setLevel(logging.DEBUG)
    assert execute.execute(**kwargs) is None
    assert logged(caplog, "%s requires argument '%s'" % (args.classname, "cycle"))


@mark.parametrize("f", [Path, str])
def test_tasks_pass(args, f):
    tasks = execute.tasks(classname=args.classname, module=f(args.module))
    assert tasks["forty_two"] == "42"


def test__get_driver_class_explicit_fail_bad_class(caplog, args):
    log.setLevel(logging.DEBUG)
    bad_class = "BadClass"
    c, module_path = execute._get_driver_class(classname=bad_class, module=args.module)
    assert c is None
    assert module_path == args.module
    assert logged(caplog, "Module %s has no class %s" % (args.module, bad_class))


def test__get_driver_class_explicit_fail_bad_name(caplog, args):
    log.setLevel(logging.DEBUG)
    bad_name = Path("bad_name")
    c, module_path = execute._get_driver_class(classname=args.classname, module=bad_name)
    assert c is None
    assert module_path is None
    assert logged(caplog, "Could not load module %s" % bad_name)


def test__get_driver_class_explicit_fail_bad_path(caplog, args, tmp_path):
    log.setLevel(logging.DEBUG)
    module = tmp_path / "not.py"
    c, module_path = execute._get_driver_class(classname=args.classname, module=module)
    assert c is None
    assert module_path is None
    assert logged(caplog, "Could not load module %s" % module)


def test__get_driver_class_explicit_fail_bad_spec(caplog, args):
    log.setLevel(logging.DEBUG)
    with patch.object(execute, "spec_from_file_location", return_value=None):
        c, module_path = execute._get_driver_class(classname=args.classname, module=args.module)
    assert c is None
    assert module_path is None
    assert logged(caplog, "Could not load module %s" % args.module)


def test__get_driver_class_explicit_pass(args):
    log.setLevel(logging.DEBUG)
    c, module_path = execute._get_driver_class(classname=args.classname, module=args.module)
    assert c
    assert c.__name__ == "TestDriver"
    assert module_path == args.module


def test__get_driver_class_implicit_pass(args):
    log.setLevel(logging.DEBUG)
    with patch.object(Path, "cwd", return_value=fixture_path()):
        c, module_path = execute._get_driver_class(classname=args.classname, module=args.module)
    assert c
    assert c.__name__ == "TestDriver"
    assert module_path == args.module


def test__get_driver_module_explicit_absolute_fail_syntax_error(args, caplog, tmp_path):
    log.setLevel(logging.ERROR)
    module = tmp_path / "module.py"
    module.write_text("syntax error\n%s" % args.module.read_text())
    assert module.is_absolute()
    assert not execute._get_driver_module_explicit(module=module)
    # If the module is found but fails to load, a traceback will be logged:
    assert logged(caplog, "Traceback (most recent call last):")
    assert logged(caplog, "SyntaxError: invalid syntax")


def test__get_driver_module_explicit_absolute_fail_bad_path(args):
    assert args.module.is_absolute()
    module = args.module.with_suffix(".bad")
    assert not execute._get_driver_module_explicit(module=module)


def test__get_driver_module_explicit_absolute_pass(args):
    assert args.module.is_absolute()
    assert execute._get_driver_module_explicit(module=args.module)


def test__get_driver_module_explicit_relative_fail_bad_path(args):
    args.module = Path(os.path.relpath(args.module)).with_suffix(".bad")
    assert not args.module.is_absolute()
    assert not execute._get_driver_module_explicit(module=args.module)


def test__get_driver_module_explicit_relative_pass(args):
    args.module = Path(os.path.relpath(args.module))
    assert not args.module.is_absolute()
    assert execute._get_driver_module_explicit(module=args.module)


def test__get_driver_module_implicit_pass_full_package():
    assert execute._get_driver_module_implicit("uwtools.tests.fixtures.testdriver")


def test__get_driver_module_implicit_pass():
    with patch.object(sys, "path", [str(fixture_path()), *sys.path]):
        assert execute._get_driver_module_implicit("testdriver")


def test__get_driver_module_implicit_fail():
    assert not execute._get_driver_module_implicit("no.such.module")
