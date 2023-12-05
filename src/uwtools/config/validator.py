"""
Support for validating a config using JSON Schema.
"""

import json
from typing import List, Union

import jsonschema

from uwtools.config.formats.yaml import YAMLConfig
from uwtools.logging import log
from uwtools.types import DefinitePath

# Public functions


def validate_yaml(schema_file: DefinitePath, config: YAMLConfig) -> bool:
    """
    Check whether the given config conforms to the given JSON Schema spec and whether any filesystem
    paths it identifies do not exist.

    :param schema_file: The JSON Schema file to use for validation.
    :param config: The config to validate.
    :return: Did the YAML file conform to the schema?
    """
    with open(schema_file, "r", encoding="utf-8") as f:
        schema = json.load(f)
    config.dereference()
    # Collect and report on schema-validation errors.
    errors = _validation_errors(config.data, schema)
    log_method = log.error if errors else log.info
    log_method("%s schema-validation error%s found", len(errors), "" if len(errors) == 1 else "s")
    for error in errors:
        for line in str(error).split("\n"):
            log.error(line)
    # It's pointless to evaluate an invalid config, so return now if that's the case.
    if errors:
        return False
    # If no issues were detected, report success.
    return True


# Private functions


def _validation_errors(config: Union[dict, list], schema: dict) -> List[str]:
    """
    Identify schema-validation errors.
    """
    validator = jsonschema.Draft202012Validator(schema)
    return list(validator.iter_errors(config))
