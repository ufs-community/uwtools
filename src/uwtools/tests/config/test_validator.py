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
def schema() -> dict[str, Any]:
    return {
        "additionalProperties": False,
        "properties": {
            "color": {
                "enum": ["blue", "red"],
                "type": "string",
            },
            "cycle": {
                "type": "datetime",
            },
            "dir": {
                "format": "uri",
                "type": "string",
            },
            "leadtime": {
                "type": "timedelta",
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
    path.write_text(json.dumps(schema))
    return path


# Helpers


def mock_extend(real_extend, msg, *args_outer, **kwargs_outer):
    """
    A mock to replace jsonschema.validators.extend.

    Returns a function that, when called the first time, raises a TypeError with the specified
    message; and when called a second time makes the call that would have happened if no mocking had
    been done.

    :param real_extend: The actual, unmocked jsonschema.validators.extend.
    :param msg: The message to associate with the TypeError.
    """

    def uwvalidator(*args_inner, **kwargs_inner):
        try:
            raise exceptions.pop()
        except IndexError:
            uwvalidator = real_extend(*args_outer, **kwargs_outer)
            return uwvalidator(*args_inner, **kwargs_inner)

    exceptions = [TypeError(msg)]
    return uwvalidator


def write_as_json(data: dict[str, Any], path: Path) -> Path:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2))
    return path


# Test functions


def test_config_validator_bundle(logged):
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
    ("schema", "config"),
    [
        ({"type": "boolean"}, True),  # bool
        ({"type": "number"}, 3.14),  # float
        ({"type": "integer"}, 42),  # int
        ({"type": "array"}, [1, 2, 3]),  # list
        ({"type": "string"}, "foo"),  # str
    ],
)
def test_config_validator_validate__alt_types(schema, config):
    assert validator.validate(schema=schema, desc="test", config=config) is True


def test_config_validator_validate__dict(config, schema):
    assert validator.validate(schema=schema, desc="test", config=config)


def test_config_validator_validate__fail_quantifier_any_of(caplog):
    log.setLevel(logging.DEBUG)
    schema = {
        "additionalProperties": False,
        "anyOf": [
            {"if": {"not": {"required": ["flower"]}}, "then": {"required": ["color"]}},
            {"if": {"not": {"required": ["color"]}}, "then": {"required": ["flower"]}},
        ],
        "properties": {"color": {"type": "string"}, "flower": {"type": "string"}},
        "type": "object",
    }
    messages = lambda: "\n".join(caplog.messages)
    ok = partial(validator.validate, schema, "test")
    for good in [{"color": "blue", "flower": "rose"}, {"color": "blue"}, {"flower": "rose"}]:
        assert ok(good)
        assert messages() == "Schema validation succeeded for test"
        caplog.clear()
    bad: dict
    for bad in [{}]:
        assert not ok(bad)
        expected = """
        1 schema-validation error found in test
        Error at top level:
          %s is not valid under any of the given schemas
          Candidate rules are:
            'color' is a required property
            'flower' is a required property
          At least one must match.
        """
        assert messages() == dedent(expected % bad).strip()
        caplog.clear()


def test_config_validator_validate__fail_quantifier_one_of(caplog):
    log.setLevel(logging.DEBUG)
    schema = {
        "additionalProperties": False,
        "oneOf": [{"required": ["color"]}, {"required": ["flower"]}],
        "properties": {"color": {"type": "string"}, "flower": {"type": "string"}},
        "type": "object",
    }
    messages = lambda: "\n".join(caplog.messages)
    ok = partial(validator.validate, schema, "test")
    for good in [{"color": "blue"}, {"flower": "rose"}]:
        assert ok(good)
        assert messages() == "Schema validation succeeded for test"
        caplog.clear()
    for bad in [{"color": "blue", "flower": "rose"}]:
        assert not ok(bad)
        expected = """
        1 schema-validation error found in test
        Error at top level:
          %s is valid under each of {'required': ['flower']}, {'required': ['color']}
          Exactly one must match.
        """
        assert messages() == dedent(expected % bad).strip()
        caplog.clear()
    for bad in [{}]:
        assert not ok(bad)
        expected = """
        1 schema-validation error found in test
        Error at top level:
          %s is not valid under any of the given schemas
          Candidate rules are:
            'color' is a required property
            'flower' is a required property
          Exactly one must match.
        """
        assert messages() == dedent(expected % bad).strip()
        caplog.clear()


def test_config_validator_validate__fail_bad_enum_val(config, logged, schema):
    config["color"] = "yellow"  # invalid enum value
    assert not validator.validate(schema=schema, desc="test", config=config)
    assert logged("1 schema-validation error found")
    assert logged("'yellow' is not one of")


def test_config_validator_validate__fail_bad_number_val(config, logged, schema):
    config["number"] = "string"  # invalid number value
    assert not validator.validate(schema=schema, desc="test", config=config)
    assert logged("1 schema-validation error found")
    assert logged("'string' is not of type 'number'")


def test_config_validator_validate__fail_top_level(logged):
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
    ("config_data", "config_path"), [(True, None), (None, True), (None, None), (True, True)]
)
def test_config_validator_validate_check_config(config_data, config_path):
    f = partial(validator.validate_check_config, config_data, config_path)
    if config_data is None or config_path is None:
        assert f() is None
    else:
        with raises(TypeError) as e:
            f()
        assert str(e.value) == "Specify at most one of config_data, config_path"


def test_config_validator_validate_internal__no(logged, schema_file):
    with (
        patch.object(validator, "resource_path", return_value=schema_file.parent),
        raises(UWConfigError) as e,
    ):
        validator.validate_internal(schema_name="a", desc="test", config_data={"color": "orange"})
    assert logged("Error at color:")
    assert logged("  'orange' is not one of ['blue', 'red']")
    assert str(e.value) == "YAML validation errors"


def test_config_validator_validate_internal__ok(schema_file):
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
    path.write_text(json.dumps(d))
    with patch.object(validator, "resource_path", return_value=path) as resource_path:
        r = validator._registry()
        assert r.get_or_retrieve("urn:uwtools:foo-bar").value.contents == d
    resource_path.assert_called_once_with("jsonschema/foo-bar.jsonschema")


@mark.parametrize("msg", [validator.PRE_4_18_JSONSCHEMA_MSG, "other"])
@mark.parametrize("pre_4_18_jsonschema", [True, False])
def test_config_validator__validation_errors__fail(config, msg, pre_4_18_jsonschema, schema):
    config["color"] = "yellow"
    if pre_4_18_jsonschema:
        mock = partial(mock_extend, validator.validators.extend, msg)
        with patch.object(validator.validators, "extend", mock):
            if msg == "other":
                with raises(TypeError) as e:
                    validator._validation_errors(config, schema)
                assert str(e.value) == "other"
                return
            errors = validator._validation_errors(config, schema)
    else:
        errors = validator._validation_errors(config, schema)
    assert len(errors) == 1


@mark.parametrize("pre_4_18_jsonschema", [True, False])
def test_config_validator__validation_errors__pass(config, pre_4_18_jsonschema, schema, tmp_path):
    if pre_4_18_jsonschema:
        # For an older jsonschema, ensure that the resolver mechanism gets exercised by this test by
        # replacing a schema value with a $ref value and arranging for the validator code to load an
        # appropriate schema file defined by this test.
        ref_schema = tmp_path / "ref.jsonschema"
        ref_schema.write_text(json.dumps({"type": "number"}))
        schema["properties"]["number"] = {"$ref": "urn:uwtools:ref"}
        mock = partial(mock_extend, validator.validators.extend, validator.PRE_4_18_JSONSCHEMA_MSG)
        with (
            patch.object(validator, "resource_path", return_value=tmp_path),
            patch.object(validator.validators, "extend", mock),
        ):
            assert not validator._validation_errors(config, schema)
    else:
        assert not validator._validation_errors(config, schema)
