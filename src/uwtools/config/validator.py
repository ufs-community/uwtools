"""
Support for validating a config using JSON Schema.
"""

import json
from pathlib import Path
from typing import List, Optional, Union

import jsonschema
from referencing import Registry, Resource
from referencing.jsonschema import DRAFT202012

from uwtools.config.formats.yaml import YAMLConfig
from uwtools.logging import log
from uwtools.utils.file import resource_path

# Public functions


def validate_yaml(
    schema_file: Path, config: Union[dict, YAMLConfig, Optional[Path]] = None
) -> bool:
    """
    Report any errors arising from validation of the given config against the given JSON Schema.

    :param schema_file: The JSON Schema file to use for validation.
    :param config: The config to validate.
    :return: Did the YAML file conform to the schema?
    """
    with open(schema_file, "r", encoding="utf-8") as f:
        schema = json.load(f)
    cfgobj = _prep_config(config)
    errors = _validation_errors(cfgobj.data, schema)
    log_method = log.error if errors else log.info
    log_msg = "%s UW schema-validation error%s found"
    log_method(log_msg, len(errors), "" if len(errors) == 1 else "s")
    for error in errors:
        for line in str(error).split("\n"):
            log.error(line)
    return not bool(errors)


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


def _validation_errors(config: Union[dict, list], schema: dict) -> List[str]:
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
    validator = jsonschema.Draft202012Validator(schema, registry=registry)
    return list(validator.iter_errors(config))
