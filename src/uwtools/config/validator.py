"""
Support for validating a config using JSON Schema.
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta
from functools import cache
from pathlib import Path
from typing import TYPE_CHECKING, Union

from jsonschema import Draft202012Validator, validators
from jsonschema._utils import Unset
from referencing import Registry, Resource
from referencing.jsonschema import DRAFT202012

from uwtools.config.formats.yaml import YAMLConfig
from uwtools.config.support import UWYAMLGlob
from uwtools.exceptions import UWConfigError
from uwtools.logging import INDENT, log
from uwtools.utils.file import resource_path

if TYPE_CHECKING:
    from jsonschema.exceptions import ValidationError

# Public functions

JSONValueT = Union[bool, dict, float, int, list, str]
ConfigDataT = Union[JSONValueT, YAMLConfig]
ConfigPathT = Union[str, Path]


def bundle(schema: dict, keys: list | None = None) -> dict:
    """
    Bundle a schema by dereferencing links to other schemas.

    :param schema: A JSON Schema.
    :param keys: Keys leading up to this block. Internal use only, do not manually specify.
    :returns: The bundled schema.
    """
    ref = "$ref"
    bundled = {}
    for k, v in schema.items():
        newkeys = [*(keys or []), k]
        key_path = ".".join(newkeys)
        if isinstance(v, dict):
            if list(v.keys()) == [ref] and v[ref].startswith("urn:uwtools:"):
                # i.e. the current key's value is of the form: {"$ref": "urn:uwtools:.*"}
                uri = v[ref]
                log.debug("Bundling referenced schema %s at key path: %s", uri, key_path)
                bundled[k] = bundle(_registry().get_or_retrieve(uri).value.contents, newkeys)
            else:
                log.debug("Bundling dict value at key path: %s", key_path)
                bundled[k] = bundle(v, newkeys)
        else:
            log.debug("Bundling %s value at key path: %s", type(v).__name__, key_path)
            bundled[k] = v
    return bundled


def internal_schema_file(schema_name: str) -> Path:
    """
    Return the path to the internal JSON Schema file for a given driver name.

    :param schema_name: Name of uwtools schema to validate the config against.
    """
    return resource_path("jsonschema") / f"{schema_name}.jsonschema"


def validate(schema: dict, desc: str, config: JSONValueT) -> bool:
    """
    Report any errors arising from validation of the given config against the given JSON Schema.

    :param schema: The JSON Schema to use for validation.
    :param desc: A description of the config being validated, for logging.
    :param config: The config to validate.
    :return: Did the YAML file conform to the schema?
    """
    errors = _validation_errors(config, schema)
    if valid := not bool(errors):
        log.info("Schema validation succeeded for %s", desc)
    else:
        nerr = len(errors)
        log.error("%s schema-validation error%s found in %s", nerr, "" if nerr == 1 else "s", desc)
        for error in errors:
            location = ".".join(str(k) for k in error.path) if error.path else "top level"
            log.error("Error at %s:", location)
            quantifiers = {"allOf": "All", "anyOf": "At least one", "oneOf": "Exactly one"}
            if error.validator in quantifiers:
                pre = quantifiers[str(error.validator)]
                log.error("%s%s of the following must hold:", INDENT, pre)
                items = error.context or error.validator_value
                assert not isinstance(items, Unset)
                for item in items:
                    msg = item.message if hasattr(item, "message") else item
                    log.error("%s%s", INDENT * 2, msg)
            else:
                log.error("%s%s", INDENT, error.message)
    return valid


def validate_check_config(
    config_data: ConfigDataT | None = None, config_path: ConfigPathT | None = None
) -> None:
    """
    Enforce mutual exclusivity of config_* arguments.

    :param config_data: A config to validate.
    :param config_path: A path to a file containing a config to validate.
    :raises: TypeError if both config_* arguments specified.
    """
    if config_data is not None and config_path is not None:
        msg = "Specify at most one of config_data, config_path"
        raise TypeError(msg)


def validate_internal(
    schema_name: str,
    desc: str,
    config_data: ConfigDataT | None = None,
    config_path: ConfigPathT | None = None,
) -> None:
    """
    Validate a config against a uwtools-internal schema.

    Specify at most one of config_data or config_path. If no config is specified, ``stdin`` is read
    and will be parsed as YAML and then validated.

    :param schema_name: Name of uwtools schema to validate the config against.
    :param desc: A description of the config being validated, for logging.
    :param config_data: A config to validate.
    :param config_path: A path to a file containing a config to validate.
    :raises: TypeError if both config_* arguments specified.
    """
    validate_check_config(config_data, config_path)
    log.info("Validating config against internal schema: %s", schema_name)
    validate_external(
        schema_file=internal_schema_file(schema_name),
        desc=desc,
        config_data=config_data,
        config_path=config_path,
    )


def validate_external(
    schema_file: Path,
    desc: str,
    config_data: ConfigDataT | None = None,
    config_path: ConfigPathT | None = None,
) -> None:
    """
    Validate a YAML config against the JSON Schema in the given schema file.

    Specify at most one of config_data or config_path. If no config is specified, ``stdin`` is read
    and will be parsed as YAML and then validated.

    :param schema_file: The JSON Schema file to use for validation.
    :param desc: A description of the config being validated, for logging.
    :param config_data: A config to validate.
    :param config_path: A path to a file containing a config to validate.
    :raises: TypeError if both config_* arguments specified.
    """
    validate_check_config(config_data, config_path)
    config: JSONValueT
    if config_data is None:
        config = YAMLConfig(config_path).dereference().data
    elif isinstance(config_data, YAMLConfig):
        config = config_data.data
    else:
        config = config_data
    if not str(schema_file).startswith(str(resource_path())):
        log.debug("Validating config against external schema file: %s", schema_file)
    schema = json.loads(schema_file.read_text())
    if not validate(schema=schema, desc=desc, config=config):
        msg = "YAML validation errors"
        raise UWConfigError(msg)


# Private functions


@cache
def _registry() -> Registry:
    """
    Return a JSON Schema registry resolving urn:uwtools:* references.
    """

    # See https://github.com/python-jsonschema/referencing/issues/61 about typing issues.

    def retrieve(uri: str) -> Resource:
        name = uri.split(":")[-1]
        return Resource(
            contents=json.loads(resource_path(f"jsonschema/{name}.jsonschema").read_text()),
            specification=DRAFT202012,
        )  # type: ignore[call-arg]

    return Registry(retrieve=retrieve)  # type: ignore[call-arg]


def _validation_errors(config: JSONValueT, schema: dict) -> list[ValidationError]:
    """
    Identify schema-validation errors.

    :param config: A config to validate.
    :param schema: JSON Schema to validate the config against.
    :return: Any validation errors.
    """
    base = Draft202012Validator
    type_checker = (
        base.TYPE_CHECKER.redefine(
            "fs_src", lambda _, x: any(isinstance(x, t) for t in [str, UWYAMLGlob])
        )
        .redefine("datetime", lambda _, x: isinstance(x, datetime))
        .redefine("timedelta", lambda _, x: isinstance(x, timedelta))
    )
    uwvalidator = validators.extend(base, type_checker=type_checker)
    validator = uwvalidator(schema, registry=_registry())
    return list(validator.iter_errors(config))
