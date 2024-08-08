# pylint: disable=missing-function-docstring,protected-access,redefined-outer-name

import datetime as dt
import logging
import os
import sys
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


@mark.parametrize(
    "classname",
    [
        "Assets",
        "AssetsCycleBased",
        "AssetsCycleLeadtimeBased",
        "AssetsTimeInvariant",
        "Driver",
        "DriverCycleBased",
        "DriverCycleLeadtimeBased",
        "DriverTimeInvariant",
    ],
)
def test_driver(classname):
    assert getattr(driver_api, classname) is getattr(driver_lib, classname)


def test__get_driver_module_implicit():
    pass


@mark.parametrize("key,val", [("batch", True), ("leadtime", 6)])
def test_execute_fail_bad_args(caplog, key, kwargs, val):
    kwargs.update({"cycle": dt.datetime.now(), key: val})
    assert driver_api.execute(**kwargs) is False
    assert logged(caplog, f"TestDriver does not accept argument '{key}'")


def test_execute_fail_stdin_not_ok(kwargs):
    kwargs["config"] = None
    kwargs["cycle"] = dt.datetime.now()
    kwargs["stdin_ok"] = False
    with raises(UWError) as e:
        driver_api.execute(**kwargs)
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


def test__get_driver_module_explicit_absolute_fail(args):
    assert args.module.is_absolute()
    module = str(args.module.with_suffix(".bad"))
    assert not driver_api._get_driver_module_explicit(module=module)


def test__get_driver_module_explicit_absolute_pass(args):
    assert args.module.is_absolute()
    module = str(args.module)
    assert driver_api._get_driver_module_explicit(module=module)


def test__get_driver_module_explicit_relative_fail(args):
    args.module = Path(os.path.relpath(args.module)).with_suffix(".bad")
    assert not args.module.is_absolute()
    module = str(args.module)
    assert not driver_api._get_driver_module_explicit(module=module)


def test__get_driver_module_explicit_relative_pass(args):
    args.module = Path(os.path.relpath(args.module))
    assert not args.module.is_absolute()
    module = str(args.module)
    assert driver_api._get_driver_module_explicit(module=module)


def test__get_driver_module_implicit_pass_full_package():
    assert driver_api._get_driver_module_implicit("uwtools.tests.fixtures.testdriver")


def test__get_driver_module_implicit_pass():
    with patch.object(sys, "path", [str(fixture_path()), *sys.path]):
        assert driver_api._get_driver_module_implicit("testdriver")


def test__get_driver_module_implicit_fail():
    assert not driver_api._get_driver_module_implicit("no.such.module")
