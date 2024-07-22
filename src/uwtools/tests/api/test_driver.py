# pylint: disable=missing-class-docstring,missing-function-docstring,protected-access,redefined-outer-name

import datetime as dt
import logging
from pathlib import Path
from types import SimpleNamespace as ns
from unittest.mock import patch

from pytest import fixture, mark, raises

from uwtools.api import driver as driver_api
from uwtools.drivers import driver as driver_lib
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
        task="eighty_eight",
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


@mark.parametrize("classname", driver_api._CLASSNAMES)
def test_driver(classname):
    assert getattr(driver_api, classname) is getattr(driver_lib, classname)


def test__get_driver_module_implicit():
    pass


def test_execute_fail_stdin_not_ok(kwargs):
    kwargs["config"] = None
    kwargs["stdin_ok"] = False
    with raises(UWError) as e:
        driver_api.execute(**kwargs)
    assert str(e.value) == "Set stdin_ok=True to permit read from stdin"


def test_execute_pass(caplog, kwargs, tmp_path):
    kwargs["cycle"] = dt.datetime.now()
    log.setLevel(logging.DEBUG)
    graph_file = tmp_path / "g.dot"
    graph_code = "DOT code"
    kwargs["graph_file"] = graph_file
    with patch.object(driver_api, "graph", return_value=graph_code):
        assert driver_api.execute(**kwargs) is True
    assert regex_logged(caplog, "Instantiated %s with" % kwargs["classname"])
    with open(graph_file, "r", encoding="utf-8") as f:
        assert f.read().strip() == graph_code


def test_execute_fail_cannot_load_driver_class(kwargs):
    kwargs["module"] = "bad_module_name"
    assert driver_api.execute(**kwargs) is False


def test_tasks_fail(args, caplog, tmp_path):
    module = tmp_path / "not.py"
    tasks = driver_api.tasks(classname=args.classname, module=module)
    assert tasks == {}
    assert logged(
        caplog, "Could not get tasks from class %s in module %s" % (args.classname, module)
    )


def test_tasks_fail_no_cycle(args, caplog, kwargs):
    log.setLevel(logging.DEBUG)
    assert driver_api.execute(**kwargs) is False
    assert logged(caplog, "%s requires argument '%s'" % (args.classname, "cycle"))


def test_tasks_pass(args):
    tasks = driver_api.tasks(classname=args.classname, module=args.module)
    assert tasks["eighty_eight"] == "88"


def test__get_driver_class_explicit_fail_bad_class(caplog, args):
    log.setLevel(logging.DEBUG)
    bad_class = "BadClass"
    c = driver_api._get_driver_class(classname=bad_class, module=args.module)
    assert c is None
    assert logged(caplog, "Module %s has no class %s" % (args.module, bad_class))


def test__get_driver_class_explicit_fail_bad_name(caplog, args):
    log.setLevel(logging.DEBUG)
    bad_name = "bad_name"
    c = driver_api._get_driver_class(classname=args.classname, module=bad_name)
    assert c is None
    assert logged(caplog, "Could not load module %s" % bad_name)


def test__get_driver_class_explicit_fail_bad_path(caplog, args, tmp_path):
    log.setLevel(logging.DEBUG)
    module = tmp_path / "not.py"
    c = driver_api._get_driver_class(classname=args.classname, module=module)
    assert c is None
    assert logged(caplog, "Could not load module %s" % module)


def test__get_driver_class_explicit_fail_bad_spec(caplog, args):
    log.setLevel(logging.DEBUG)
    with patch.object(driver_api, "spec_from_file_location", return_value=None):
        c = driver_api._get_driver_class(classname=args.classname, module=args.module)
    assert c is None
    assert logged(caplog, "Could not load module %s" % args.module)


def test__get_driver_class_explicit_pass(args):
    log.setLevel(logging.DEBUG)
    c = driver_api._get_driver_class(classname=args.classname, module=args.module)
    assert c
    assert c.__name__ == "TestDriver"


def test__get_driver_class_implicit_pass(args):
    log.setLevel(logging.DEBUG)
    with patch.object(Path, "cwd", return_value=fixture_path()):
        c = driver_api._get_driver_class(classname=args.classname, module=args.module)
        assert c
        assert c.__name__ == "TestDriver"
