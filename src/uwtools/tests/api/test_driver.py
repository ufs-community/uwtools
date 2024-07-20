# pylint: disable=missing-function-docstring,protected-access,missing-class-docstring,redefined-outer-name

import logging
from pathlib import Path
from types import SimpleNamespace as ns
from unittest.mock import DEFAULT as D
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
        module="testdriver",
        module_dir=fixture_path("testdriver.py").parent,
        schema_file=fixture_path("testdriver.jsonschema"),
        task="eighty_eight",
    )


@fixture
def kwargs(args):
    return dict(
        classname=args.classname,
        config=args.config,
        module=args.module,
        module_dir=args.module_dir,
        schema_file=args.schema_file,
        task=args.task,
    )


# Tests


@mark.parametrize("classname", driver_api._CLASSNAMES)
def test_driver(classname):
    assert getattr(driver_api, classname) is getattr(driver_lib, classname)


def test_execute_fail_bad_module_dir(kwargs, tmp_path):
    kwargs["module_dir"] = tmp_path
    assert driver_api.execute(**kwargs) is False


def test_execute_fail_stdin_not_ok(kwargs):
    kwargs["config"] = None
    kwargs["stdin_ok"] = False
    with raises(UWError) as e:
        driver_api.execute(**kwargs)
    assert str(e.value) == "Set stdin_ok=True to permit read from stdin"


def test_execute_pass(args, caplog, kwargs, tmp_path):
    log.setLevel(logging.DEBUG)
    graph_file = tmp_path / "g.dot"
    graph_code = "DOT code"
    kwargs["graph_file"] = graph_file
    with patch.multiple(driver_api, getfullargspec=D, graph=D, _get_driver_class=D) as mocks:
        mocks["getfullargspec"].return_value = ns(args=["batch", "cycle", "leadtime"])
        mocks["graph"].return_value = graph_code
        assert driver_api.execute(**kwargs) is True
    assert regex_logged(caplog, "Instantiated %s with args" % kwargs["classname"])
    mocks["_get_driver_class"].assert_called_once_with(
        classname=args.classname, module=args.module, module_dir=args.module_dir
    )
    mocked_class = mocks["_get_driver_class"]()
    mocked_class.assert_called_once_with(
        batch=False,
        config=args.config,
        cycle=None,
        dry_run=False,
        key_path=None,
        leadtime=None,
        schema_file=args.schema_file,
    )
    with open(graph_file, "r", encoding="utf-8") as f:
        assert f.read().strip() == graph_code


def test_tasks_fail(args, caplog, tmp_path):
    tasks = driver_api.tasks(classname=args.classname, module=args.module, module_dir=tmp_path)
    assert tasks == {}
    assert logged(
        caplog,
        "Could not get tasks from class %s in module %s in %s"
        % (args.classname, args.module, tmp_path),
    )


def test_tasks_pass(args):
    tasks = driver_api.tasks(
        classname=args.classname,
        module=args.module,
        module_dir=args.module_dir,
    )
    assert tasks["eighty_eight"] == "88"


def test__get_driver_class_explicit_module_dir_fail_bad_class(caplog, args):
    log.setLevel(logging.DEBUG)
    bad_class = "BadClass"
    c = driver_api._get_driver_class(
        classname=bad_class, module=args.module, module_dir=args.module_dir
    )
    assert c is None
    assert logged(caplog, "Module %s has no class %s" % (args.module, bad_class))


def test__get_driver_class_explicit_module_dir_fail_bad_name(caplog, args):
    log.setLevel(logging.DEBUG)
    bad_name = "bad_name"
    c = driver_api._get_driver_class(
        classname=args.classname, module=bad_name, module_dir=args.module_dir
    )
    assert c is None
    assert logged(caplog, "Could not load module %s" % bad_name)


def test__get_driver_class_explicit_module_dir_fail_bad_path(caplog, args, tmp_path):
    log.setLevel(logging.DEBUG)
    c = driver_api._get_driver_class(
        classname=args.classname, module=args.module, module_dir=tmp_path
    )
    assert c is None
    assert logged(caplog, "Could not load module %s" % args.module)


def test__get_driver_class_explicit_module_dir_pass(args):
    log.setLevel(logging.DEBUG)
    c = driver_api._get_driver_class(
        classname=args.classname, module=args.module, module_dir=args.module_dir
    )
    assert c
    assert c.__name__ == "TestDriver"


def test__get_driver_class_implicit_module_dir_fail_bad_class(caplog, args):
    log.setLevel(logging.DEBUG)
    bad_class = "BadClass"
    with patch.object(Path, "cwd", return_value=args.module_dir):
        c = driver_api._get_driver_class(classname=bad_class, module=args.module)
    assert c is None
    assert logged(caplog, "Module %s has no class %s" % (args.module, bad_class))


def test__get_driver_class_implicit_module_dir_fail_bad_name(caplog, args):
    log.setLevel(logging.DEBUG)
    bad_name = "bad_name"
    with patch.object(Path, "cwd", return_value=args.module_dir):
        c = driver_api._get_driver_class(classname=args.classname, module=bad_name)
    assert c is None
    assert logged(caplog, "Could not load module %s" % bad_name)


def test__get_driver_class_implicit_module_dir_fail_bad_path(caplog, args, tmp_path):
    log.setLevel(logging.DEBUG)
    with patch.object(Path, "cwd", return_value=tmp_path):
        c = driver_api._get_driver_class(classname=args.classname, module=args.module)
    assert c is None
    assert logged(caplog, "Could not load module %s" % args.module)


def test__get_driver_class_implicit_module_dir_pass(args):
    log.setLevel(logging.DEBUG)
    with patch.object(Path, "cwd", return_value=args.module_dir):
        c = driver_api._get_driver_class(classname=args.classname, module=args.module)
        assert c
        assert c.__name__ == "TestDriver"
