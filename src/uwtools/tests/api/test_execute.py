import os
import sys
from pathlib import Path
from types import SimpleNamespace as ns
from unittest.mock import Mock, patch

from pytest import fixture, mark, raises

from uwtools.api import execute
from uwtools.exceptions import UWError
from uwtools.tests.support import fixture_path

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


@mark.parametrize(("key", "val"), [("batch", True), ("leadtime", 6)])
def test_execute__fail_bad_args(key, kwargs, logged, utc, val):
    kwargs.update({"cycle": utc(), key: val})
    assert execute.execute(**kwargs) is None
    assert logged(f"TestDriver does not accept argument '{key}'")


def test_execute__fail_bad_task(kwargs, logged, utc):
    kwargs.update({"cycle": utc(), "task": "foo"})
    assert execute.execute(**kwargs) is None
    assert logged("TestDriver driver has no task 'foo'")


def test_execute__fail_cannot_load_driver_class(kwargs):
    kwargs["module"] = "bad_module_name"
    assert execute.execute(**kwargs) is None


def test_execute__fail_stdin_not_ok(kwargs, utc):
    kwargs["config"] = None
    kwargs["cycle"] = utc()
    kwargs["stdin_ok"] = False
    with raises(UWError) as e:
        execute.execute(**kwargs)
    assert str(e.value) == "Set stdin_ok=True to permit read from stdin"


@mark.parametrize("graph", [True, False])
@mark.parametrize("remove", [[], ["schema_file"]])
def test_execute__pass(graph, kwargs, logged, remove, tmp_path, utc):
    for kwarg in remove:
        del kwargs[kwarg]
    kwargs["cycle"] = utc()
    if graph:
        graph_file = tmp_path / "g.dot"
        graph_code = "DOT code"
        kwargs["graph_file"] = graph_file
    with (
        patch.object(execute, "_get_driver_class") as gdc,
        patch.object(execute, "getfullargspec") as gfa,
        patch.object(execute, "tasknames", return_value=["forty_two"]),
    ):
        node = Mock(graph=graph_code) if graph else Mock()
        node.ref = 42
        driverobj = Mock()
        driverobj.forty_two.return_value = node
        class_ = Mock(return_value=driverobj)
        setattr(class_, "__name__", "test")
        gdc.return_value = class_
        gfa().args = {"batch", "cycle"}
        val = execute.execute(**kwargs)
        assert val
        assert val.ref == 42
    assert class_.call_args.kwargs["schema_file"] == (
        None if "schema_file" in remove else Path(kwargs["schema_file"])
    )
    assert logged("Instantiated %s with" % kwargs["classname"])
    if graph:
        assert graph_file.read_text().strip() == graph_code


def test_tasks__fail(args, logged, tmp_path):
    module = tmp_path / "not.py"
    tasks = execute.tasks(classname=args.classname, module=module)
    assert tasks == {}
    assert logged("Could not get tasks from class %s in module %s" % (args.classname, module))


def test_tasks__fail_no_cycle(args, kwargs, logged):
    assert execute.execute(**kwargs) is None
    assert logged("%s requires argument '%s'" % (args.classname, "cycle"))


@mark.parametrize("f", [Path, str])
def test_tasks__pass(args, f):
    tasks = execute.tasks(classname=args.classname, module=f(args.module))
    assert tasks["forty_two"] == "Forty Two."


@mark.parametrize("case", ["bad_class", "bad_name", "bad_path", "bad_spec"])
def test__get_driver_class__fail(args, case, logged, tmp_path):
    classname, module = args.classname, args.module
    if case == "bad_class":
        classname = "BadClass"
    elif case == "bad_name":
        module = Path("bad_name")
    elif case == "bad_path":
        module = tmp_path / "not.py"
    spec_kwargs = (
        {"return_value": None} if case == "bad_spec" else {"wraps": execute.spec_from_file_location}
    )
    with patch.object(execute, "spec_from_file_location", **spec_kwargs):
        assert execute._get_driver_class(classname=classname, module=module) is None
    assert logged(
        "Module %s has no class %s" % (module, classname)
        if case == "bad_class"
        else "Could not load module %s" % module
    )


@mark.parametrize("cwd", [None, fixture_path()])
def test__get_driver_class__pass(args, cwd):
    with patch.object(Path, "cwd", return_value=cwd or Path.cwd()):
        c = execute._get_driver_class(classname=args.classname, module=args.module)
    assert c
    assert c.__name__ == "TestDriver"


def test__get_driver_module__explicit_absolute_fail_syntax_error(args, logged, tmp_path):
    module = tmp_path / "module.py"
    module.write_text("syntax error\n%s" % args.module.read_text())
    assert module.is_absolute()
    assert not execute._get_driver_module_explicit(module=module)
    assert module.stem not in sys.modules
    # If the module is found but fails to load, a traceback will be logged:
    assert logged("Traceback (most recent call last):")
    assert logged("SyntaxError: invalid syntax")


def test__get_driver_module__explicit_absolute_fail_bad_path(args):
    assert args.module.is_absolute()
    module = args.module.with_suffix(".bad")
    assert not execute._get_driver_module_explicit(module=module)


def test__get_driver_module__explicit_absolute_pass(args):
    assert args.module.is_absolute()
    with patch.dict(sys.modules):
        m = execute._get_driver_module_explicit(module=args.module)
        assert m
        assert sys.modules[args.module.stem] is m


def test__get_driver_module__explicit_relative_fail_bad_path(args):
    args.module = Path(os.path.relpath(args.module)).with_suffix(".bad")
    assert not args.module.is_absolute()
    assert not execute._get_driver_module_explicit(module=args.module)


def test__get_driver_module__explicit_relative_pass(args):
    args.module = Path(os.path.relpath(args.module))
    assert not args.module.is_absolute()
    assert execute._get_driver_module_explicit(module=args.module)


def test__get_driver_module__implicit_pass_full_package():
    assert execute._get_driver_module_implicit("uwtools.tests.fixtures.testdriver")


def test__get_driver_module__implicit_pass():
    with patch.object(sys, "path", [str(fixture_path()), *sys.path]):
        assert execute._get_driver_module_implicit("testdriver")


def test__get_driver_module__implicit_fail():
    assert not execute._get_driver_module_implicit("no.such.module")
