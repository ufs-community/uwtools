"""
Support for validating a config using JSON Schema.
"""

import json
from pathlib import Path
from typing import Optional, Union

from jsonschema import Draft202012Validator
from jsonschema.exceptions import ValidationError
from referencing import Registry, Resource
from referencing.jsonschema import DRAFT202012

from uwtools.config.formats.yaml import YAMLConfig
from uwtools.exceptions import UWConfigError
from uwtools.logging import INDENT, log
from uwtools.utils.file import resource_path

# Public functions


def get_schema_file(schema_name: str) -> Path:
    """
    Returns the path to the JSON Schema file for a given name.

    :param schema_name: Name of uwtools schema to validate the config against.
    """
    return resource_path("jsonschema") / f"{schema_name}.jsonschema"


def validate(schema: dict, config: dict) -> bool:
    """
    Report any errors arising from validation of the given config against the given JSON Schema.

    :param schema: The JSON Schema to use for validation.
    :param config: The config to validate.
    :return: Did the YAML file conform to the schema?
    """
    errors = _validation_errors(config, schema)
    log_method = log.error if errors else log.info
    log_msg = "%s UW schema-validation error%s found"
    log_method(log_msg, len(errors), "" if len(errors) == 1 else "s")
    for error in errors:
        log.error("Error at %s:", " -> ".join(str(k) for k in error.path))
        log.error("%s%s", INDENT, error.message)
    return not bool(errors)


def validate_internal(
    schema_name: str, config: Optional[Union[dict, YAMLConfig, Path]] = None
) -> None:
    """
    Validate a config against a uwtools-internal schema.

    :param schema_name: Name of uwtools schema to validate the config against.
    :param config: The config to validate.
    :raises: UWConfigError if config fails validation.
    """

    log.info("Validating config against internal schema: %s", schema_name)
    schema_file = get_schema_file(schema_name)
    log.debug("Using schema file: %s", schema_file)
    validate_external(config=config, schema_file=schema_file)


def validate_external(
    schema_file: Path, config: Optional[Union[dict, YAMLConfig, Path]] = None
) -> None:
    """
    Validate a YAML config against the JSON Schema in the given schema file.

    :param schema_file: The JSON Schema file to use for validation.
    :param config: The config to validate.
    :raises: UWConfigError if config fails validation.
    """
    with open(schema_file, "r", encoding="utf-8") as f:
        schema = json.load(f)
    cfgobj = _prep_config(config)
    if not validate(schema=schema, config=cfgobj.data):
        raise UWConfigError("YAML validation errors")


# Private functions


def _prep_config(config: Union[dict, YAMLConfig, Optional[Path]]) -> YAMLConfig:
    """
    Ensure a dereferenced YAMLConfig object for various input types.

    :param config: The config to validate.
    :return: A dereferenced YAMLConfig object based on the input config.
    """
    cfgobj = config if isinstance(config, YAMLConfig) else YAMLConfig(config)
    cfgobj.dereference()
    return cfgobj


def _validation_errors(config: Union[dict, list], schema: dict) -> list[ValidationError]:
    """
    Identify schema-validation errors.

    :param config: A config to validate.
    :param schema: JSON Schema to validate the config against.
    :return: Any validation errors.
    """

    # See https://github.com/python-jsonschema/referencing/issues/61 about typing issues.

    def retrieve(uri: str) -> Resource:
        name = uri.split(":")[-1]
        with open(resource_path(f"jsonschema/{name}.jsonschema"), "r", encoding="utf-8") as f:
            return Resource(contents=json.load(f), specification=DRAFT202012)  # type: ignore

    registry = Registry(retrieve=retrieve)  # type: ignore
    validator = Draft202012Validator(schema, registry=registry)
    return list(validator.iter_errors(config))
