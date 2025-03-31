# pylint: disable=missing-function-docstring,protected-access,redefined-outer-name
"""
Tests for uwtools.config.validator module.
"""
import json
import logging
from functools import partial
from pathlib import Path
from textwrap import dedent
from typing import Any
from unittest.mock import Mock, patch

from pytest import fixture, mark, raises

from uwtools.config import validator
from uwtools.config.formats.yaml import YAMLConfig
from uwtools.exceptions import UWConfigError
from uwtools.logging import log
from uwtools.utils.file import resource_path

# Fixtures


@fixture
def assets(config, schema, tmp_path) -> tuple[Path, Path, YAMLConfig]:
    config_file = tmp_path / "config.yaml"
    schema_file = tmp_path / "schema.yaml"
    write_as_json(config, config_file)
    write_as_json(schema, schema_file)
    return schema_file, config_file, YAMLConfig(config_file)


@fixture
def config(tmp_path) -> dict[str, Any]:
    return {
        "color": "blue",
        "dir": str(tmp_path),
        "number": 42,
        "sub": {
            "dir": str(tmp_path),
        },
    }


@fixture
def prep_config_dict():
    return {"roses": "{{ color }}", "color": "red"}


@fixture
def rocoto_assets():
    schema_file = resource_path("jsonschema/rocoto.jsonschema")
    kwargs = {"schema_file": schema_file, "config_file": "/not/used"}
    config = {
        "workflow": {
            "cycledef": [{"spec": "202209290000 202209300000 06:00:00"}],
            "log": "/some/path/to/&FOO;",
            "tasks": {
                "metatask": {
                    "var": {"member": "foo bar baz"},
                    "task": {
                        "cores": 42,
                        "command": "some-command",
                        "walltime": "00:01:00",
                        "dependency": {
                            "taskdep": {
                                "attrs": {
                                    "task": "hello",
                                },
                            },
                        },
                    },
                },
            },
        }
    }
    return kwargs, config


@fixture
def schema() -> dict[str, Any]:
    return {
        "properties": {
            "color": {
                "enum": ["blue", "red"],
                "type": "string",
            },
            "dir": {
                "format": "uri",
                "type": "string",
            },
            "number": {"type": "number"},
            "sub": {
                "properties": {
                    "dir": {
                        "format": "uri",
                        "type": "string",
                    },
                    "type": "object",
                },
            },
        },
        "type": "object",
    }


@fixture
def schema_file(schema, tmp_path) -> Path:
    path: Path = tmp_path / "a.jsonschema"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(schema, f)
    return path


# Helpers


def write_as_json(data: dict[str, Any], path: Path) -> Path:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return path


# Test functions


def test_config_validator_bundle(logged):
    log.setLevel(logging.DEBUG)
    schema = {"fruit": {"$ref": "urn:uwtools:a"}, "flowers": None}
    with patch.object(validator, "_registry") as _registry:
        outer, inner = Mock(), Mock()
        outer.value.contents = {"a": {"$ref": "urn:uwtools:attrs"}, "b": {"name": "banana"}}
        inner.value.contents = {"name": "apple"}
        _registry().get_or_retrieve.side_effect = [outer, inner]
        bundled = validator.bundle(schema)
    assert bundled == {"fruit": {"a": {"name": "apple"}, "b": {"name": "banana"}}, "flowers": None}
    assert [_registry().get_or_retrieve.mock_calls[i].args[0] for i in (0, 1)] == [
        "urn:uwtools:a",
        "urn:uwtools:attrs",
    ]
    for msg in [
        "Bundling referenced schema urn:uwtools:a at key path: fruit",
        "Bundling referenced schema urn:uwtools:attrs at key path: fruit.a",
        "Bundling str value at key path: fruit.a.name",
        "Bundling dict value at key path: fruit.b",
        "Bundling str value at key path: fruit.b.name",
        "Bundling NoneType value at key path: flowers",
    ]:
        assert logged(msg)


def test_config_validator_internal_schema_file():
    with patch.object(validator, "resource_path", return_value=Path("/foo/bar")):
        assert validator.internal_schema_file("baz") == Path("/foo/bar/baz.jsonschema")


@mark.parametrize(
    "schema,config",
    [
        ({"type": "boolean"}, True),  # bool
        ({"type": "number"}, 3.14),  # float
        ({"type": "integer"}, 42),  # int
        ({"type": "array"}, [1, 2, 3]),  # list
        ({"type": "string"}, "foo"),  # str
    ],
)
def test_config_validator_validate_alt_types(schema, config):
    assert validator.validate(schema=schema, desc="test", config=config) is True


def test_config_validator_validate_dict(config, schema):
    assert validator.validate(schema=schema, desc="test", config=config)


def test_config_validator_validate_fail_bad_enum_val(config, logged, schema):
    log.setLevel(logging.INFO)
    config["color"] = "yellow"  # invalid enum value
    assert not validator.validate(schema=schema, desc="test", config=config)
    assert logged("1 schema-validation error found")
    assert logged("'yellow' is not one of")


def test_config_validator_validate_fail_bad_number_val(config, logged, schema):
    log.setLevel(logging.INFO)
    config["number"] = "string"  # invalid number value
    assert not validator.validate(schema=schema, desc="test", config=config)
    assert logged("1 schema-validation error found")
    assert logged("'string' is not of type 'number'")


def test_config_validator_validate_fail_top_level(logged):
    schema = {
        "additionalProperties": False,
        "properties": {"n": {"type": "integer"}},
        "required": ["n"],
        "type": "object",
    }
    config = {"x": 42}
    assert not validator.validate(schema=schema, desc="test", config=config)
    expected = """
    2 schema-validation errors found in test
    Error at top level:
      Additional properties are not allowed ('x' was unexpected)
    Error at top level:
      'n' is a required property
    """
    assert logged(dedent(expected), full=True)


@mark.parametrize(
    "config_data,config_path", [(True, None), (None, True), (None, None), (True, True)]
)
def test_config_validator_validate_check_config(config_data, config_path):
    f = partial(validator.validate_check_config, config_data, config_path)
    if config_data is None or config_path is None:
        assert f() is None
    else:
        with raises(TypeError) as e:
            f()
        assert str(e.value) == "Specify at most one of config_data, config_path"


def test_config_validator_validate_internal_no(logged, schema_file):
    with patch.object(validator, "resource_path", return_value=schema_file.parent):
        with raises(UWConfigError) as e:
            validator.validate_internal(
                schema_name="a", desc="test", config_data={"color": "orange"}
            )
    assert logged("Error at color:")
    assert logged("  'orange' is not one of ['blue', 'red']")
    assert str(e.value) == "YAML validation errors"


def test_config_validator_validate_internal_ok(schema_file):
    with patch.object(validator, "resource_path", return_value=schema_file.parent):
        validator.validate_internal(schema_name="a", desc="test", config_data={"color": "blue"})


def test_config_validator_validate_external(assets, config, schema):
    schema_file, _, cfgobj = assets
    with patch.object(validator, "validate") as validate:
        validator.validate_external(schema_file=schema_file, desc="test", config_data=cfgobj)
    validate.assert_called_once_with(schema=schema, desc="test", config=config)


def test_config_validator__registry(tmp_path):
    validator._registry.cache_clear()
    d = {"foo": "bar"}
    path = tmp_path / "foo-bar.jsonschema"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(d, f)
    with patch.object(validator, "resource_path", return_value=path) as resource_path:
        r = validator._registry()
        assert r.get_or_retrieve("urn:uwtools:foo-bar").value.contents == d
    resource_path.assert_called_once_with("jsonschema/foo-bar.jsonschema")


def test_config_validator__validation_errors_bad_enum_value(config, schema):
    config["color"] = "yellow"
    assert len(validator._validation_errors(config, schema)) == 1


def test_config_validator__validation_errors_bad_number_value(config, schema):
    config["number"] = "string"
    assert len(validator._validation_errors(config, schema)) == 1


def test_config_validator__validation_errors_pass(config, schema):
    assert not validator._validation_errors(config, schema)
