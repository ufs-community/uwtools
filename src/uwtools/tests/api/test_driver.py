# pylint: disable=missing-function-docstring,protected-access,missing-class-docstring,redefined-outer-name

import os
from unittest.mock import patch
from types import SimpleNamespace as ns
from pathlib import Path

from pytest import fixture, mark

from uwtools.api import driver as driver_api
from uwtools.drivers import driver as driver_lib
from uwtools.tests.support import fixture_path, logged


@mark.parametrize("classname", driver_api._CLASSNAMES)
def test_driver(classname):
    assert getattr(driver_api, classname) is getattr(driver_lib, classname)


@fixture
def args():
    return ns(
        classname="TestDriver",
        module="testdriver",
        module_dir=fixture_path("testdriver.py").parent,
        schema_file=fixture_path("testdriver.jsonschema"),
        task="eighty_eight",
        config=fixture_path("testdriver.yaml"),
    )


def test_tasks(args):
    assert (
        driver_api.tasks(classname=args.classname, module=args.module, module_dir=args.module_dir)[
            "eighty_eight"
        ]
        == "Doc string."
    )


def test__get_driver_class_implicit_module_dir_pass(args):
    with patch.object(Path, "cwd", return_value=args.module_dir) as m:
        assert True is driver_api.execute(
            classname=args.classname,
            module=args.module,
            schema_file=args.schema_file,
            task=args.task,
            config=args.config,
        )
    print("@@@@@@@", m.call_count)


def test__get_driver_class_implicit_module_dir_fail(args, caplog):
    assert False is driver_api.execute(
        classname=args.classname,
        module=args.module,
        schema_file=args.schema_file,
        task=args.task,
        config=args.config,
    )
    assert logged(caplog, "No module named %s on path, including %s."% (args.module, Path.cwd()))
