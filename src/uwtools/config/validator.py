"""
Support for validating a config using JSON Schema.
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta
from functools import cache
from pathlib import Path
from typing import TYPE_CHECKING, cast

from jsonschema import Draft202012Validator, RefResolver, validators

from uwtools.config.formats.yaml import YAMLConfig
from uwtools.config.support import UWYAMLGlob
from uwtools.exceptions import UWConfigError
from uwtools.logging import INDENT, log
from uwtools.utils.file import resource_path

try:
    from referencing import Registry, Resource
    from referencing.jsonschema import DRAFT202012
except ModuleNotFoundError:  # pragma: no cover
    ...

if TYPE_CHECKING:
    from jsonschema.exceptions import ValidationError


JSONSCHEMA_MSG_REGISTRY_NO_KWARG = "unexpected keyword argument 'registry'"
JSONSCHEMA_MSG_REGISTRY_UNDEFINED = "name 'Registry' is not defined"

# Types

JSONValueT = bool | dict | float | int | list | str
ConfigDataT = JSONValueT | YAMLConfig
ConfigPathT = str | Path

# Public functions


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
            log.error("%s%s", INDENT, error.message)
            quantifiers = {"anyOf": "At least one", "oneOf": "Exactly one"}
            if error.validator in quantifiers:
                if items := error.context:
                    log.error("%sCandidate rules are:", INDENT)
                    for item in items:
                        log.error("%s%s", INDENT * 2, item.message)
                log.error("%s%s must match.", INDENT, quantifiers[str(error.validator)])
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
        path = resource_path(f"jsonschema/{name}.jsonschema")
        text = json.loads(path.read_text())
        return Resource(contents=text, specification=DRAFT202012)  # type: ignore[call-arg]

    return Registry(retrieve=retrieve)  # type: ignore[call-arg]


def _resolver(schema: dict) -> RefResolver:
    """
    Return a pre-4.18 jsonschema resolver that loads schema files given a URI.

    :param schema: A schema potentially containing $ref keys.
    """

    def retrieve(uri: str) -> dict:
        name = uri.split(":")[-1]
        path = schemadir / f"{name}.jsonschema"
        text = path.read_text()
        return cast(dict, json.loads(text))

    schemadir = resource_path("jsonschema")
    return cast(RefResolver, RefResolver.from_schema(schema, handlers={"urn": retrieve}))


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
    try:
        validator = uwvalidator(schema, registry=_registry())
    except (NameError, TypeError) as e:
        msgs = [JSONSCHEMA_MSG_REGISTRY_NO_KWARG, JSONSCHEMA_MSG_REGISTRY_UNDEFINED]
        if any(msg in str(e) for msg in msgs):
            # If TypeError was raised because 'registry' is not a kwarg (true for jsonschema < 4.18)
            # or if NameError was raised because Registry was not imported (true if 'referencing' is
            # not installed, and jsonschema < 4.18 does not require it), then instantate a validator
            # using the older resolver mechanism.
            validator = uwvalidator(schema, resolver=_resolver(schema))
        else:
            # If an error was raised for some other reason, re-raise it.
            raise
    return list(validator.iter_errors(config))
