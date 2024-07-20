# pylint: disable=missing-function-docstring,protected-access,missing-class-docstring,redefined-outer-name

import logging
from pathlib import Path
from types import SimpleNamespace as ns
from unittest.mock import patch

from pytest import fixture, mark

from uwtools.api import driver as driver_api
from uwtools.drivers import driver as driver_lib
from uwtools.logging import log
from uwtools.tests.support import fixture_path, logged


@mark.parametrize("classname", driver_api._CLASSNAMES)
def test_driver(classname):
    assert getattr(driver_api, classname) is getattr(driver_lib, classname)


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


def test_tasks(args):
    tasks = driver_api.tasks(
        classname=args.classname,
        module=args.module,
        module_dir=args.module_dir,
    )
    assert tasks["eighty_eight"] == "88"


def test__get_driver_class_implicit_module_dir_fail_bad_class(caplog, args):
    log.setLevel(logging.DEBUG)
    bad_class = "BadClass"
    with patch.object(Path, "cwd", return_value=args.module_dir):
        c = driver_api._get_driver_class(classname=bad_class, module=args.module)
    assert c is None
    assert logged(caplog, "Module %s has no class %s" % (args.module, bad_class))


def test__get_driver_class_implicit_module_dir_fail_bad_path(caplog, args, tmp_path):
    log.setLevel(logging.DEBUG)
    with patch.object(Path, "cwd", return_value=tmp_path):
        c = driver_api._get_driver_class(classname=args.classname, module=args.module)
    assert c is None
    assert logged(caplog, "Could not load module %s" % args.module)


def test__get_driver_class_implicit_module_dir_fail_bad_name(caplog, args):
    log.setLevel(logging.DEBUG)
    bad_name = "bad_name"
    with patch.object(Path, "cwd", return_value=args.module_dir):
        c = driver_api._get_driver_class(classname=args.classname, module=bad_name)
    assert c is None
    assert logged(caplog, "Could not load module %s" % bad_name)


def test__get_driver_class_implicit_module_dir_pass(args):
    log.setLevel(logging.DEBUG)
    with patch.object(Path, "cwd", return_value=args.module_dir):
        c = driver_api._get_driver_class(classname=args.classname, module=args.module)
        assert c
        assert c.__name__ == "TestDriver"
