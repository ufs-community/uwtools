"""
Support for validating a config using JSON Schema.
"""

import json
from pathlib import Path
from typing import List, Optional, Union

import jsonschema

from uwtools.config.formats.yaml import YAMLConfig
from uwtools.logging import log

# Public functions


def validate_yaml(
    schema_file: Path, config: Union[dict, YAMLConfig, Optional[Path]] = None
) -> bool:
    """
    Check whether the given config conforms to the given JSON Schema spec.

    :param schema_file: The JSON Schema file to use for validation.
    :param config: The config to validate.
    :return: Did the YAML file conform to the schema?
    """
    with open(schema_file, "r", encoding="utf-8") as f:
        schema = json.load(f)
    cfgobj = _prep_config(config)
    # Collect and report on schema-validation errors.
    errors = _validation_errors(cfgobj.data, schema)
    log_method = log.error if errors else log.info
    log_method(
        "%s UW schema-validation error%s found", len(errors), "" if len(errors) == 1 else "s"
    )
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
    """
    validator = jsonschema.Draft202012Validator(schema)
    return list(validator.iter_errors(config))
