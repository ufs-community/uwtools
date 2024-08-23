# pylint: disable=missing-function-docstring,protected-access,redefined-outer-name
"""
Tests for uwtools.config.validator module.
"""
import json
import logging
from pathlib import Path
from typing import Any
from unittest.mock import patch

import yaml
from pytest import fixture, mark, raises

from uwtools.config import validator
from uwtools.config.formats.yaml import YAMLConfig
from uwtools.exceptions import UWConfigError
from uwtools.logging import log
from uwtools.tests.support import logged
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
        "number": 88,
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
                        "cores": 88,
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


@mark.skip("PM FIXME")
def test_bundle():
    pass


def test_get_schema_file():
    with patch.object(validator, "resource_path", return_value=Path("/foo/bar")):
        assert validator.get_schema_file("baz") == Path("/foo/bar/baz.jsonschema")


def test_validate(config, schema):
    assert validator.validate(schema=schema, config=config)


def test_validate_fail_bad_enum_val(caplog, config, schema):
    log.setLevel(logging.INFO)
    config["color"] = "yellow"  # invalid enum value
    assert not validator.validate(schema=schema, config=config)
    assert any(x for x in caplog.records if "1 UW schema-validation error found" in x.message)
    assert any(x for x in caplog.records if "'yellow' is not one of" in x.message)


def test_validate_fail_bad_number_val(caplog, config, schema):
    log.setLevel(logging.INFO)
    config["number"] = "string"  # invalid number value
    assert not validator.validate(schema=schema, config=config)
    assert any(x for x in caplog.records if "1 UW schema-validation error found" in x.message)
    assert any(x for x in caplog.records if "'string' is not of type 'number'" in x.message)


def test_validate_internal_no(caplog, schema_file):
    with patch.object(validator, "resource_path", return_value=schema_file.parent):
        with raises(UWConfigError) as e:
            validator.validate_internal(schema_name="a", config={"color": "orange"})
    assert logged(caplog, "Error at color:")
    assert logged(caplog, "  'orange' is not one of ['blue', 'red']")
    assert str(e.value) == "YAML validation errors"


def test_validate_internal_ok(schema_file):
    with patch.object(validator, "resource_path", return_value=schema_file.parent):
        validator.validate_internal(schema_name="a", config={"color": "blue"})


def test_validate_external(assets, config, schema):
    schema_file, _, cfgobj = assets
    with patch.object(validator, "validate") as validate:
        validator.validate_external(schema_file=schema_file, config=cfgobj)
    validate.assert_called_once_with(schema=schema, config=config)


def test_prep_config_cfgobj(prep_config_dict):
    cfgobj = validator._prep_config(config=YAMLConfig(config=prep_config_dict))
    assert isinstance(cfgobj, YAMLConfig)
    assert cfgobj == {"roses": "red", "color": "red"}


def test__prep_config_dict(prep_config_dict):
    cfgobj = validator._prep_config(config=prep_config_dict)
    assert isinstance(cfgobj, YAMLConfig)
    assert cfgobj == {"roses": "red", "color": "red"}


def test__prep_config_file(prep_config_dict, tmp_path):
    path = tmp_path / "config.yaml"
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(prep_config_dict, f)
    cfgobj = validator._prep_config(config=path)
    assert isinstance(cfgobj, YAMLConfig)
    assert cfgobj == {"roses": "red", "color": "red"}


def test__registry(tmp_path):
    validator._registry.cache_clear()
    d = {"foo": "bar"}
    path = tmp_path / "foo-bar.jsonschema"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(d, f)
    with patch.object(validator, "resource_path", return_value=path) as resource_path:
        r = validator._registry()
        assert r.get_or_retrieve("urn:uwtools:foo-bar").value.contents == d
    resource_path.assert_called_once_with("jsonschema/foo-bar.jsonschema")


def test__validation_errors_bad_enum_value(config, schema):
    config["color"] = "yellow"
    assert len(validator._validation_errors(config, schema)) == 1


def test__validation_errors_bad_number_value(config, schema):
    config["number"] = "string"
    assert len(validator._validation_errors(config, schema)) == 1


def test__validation_errors_pass(config, schema):
    assert not validator._validation_errors(config, schema)
