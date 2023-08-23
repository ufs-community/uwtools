"""
Support for validating a config using JSON Schema.
"""
import json
import logging
from pathlib import Path
from typing import List

import jsonschema

from uwtools.config.core import YAMLConfig

# Public functions


def config_is_valid(config_file: str, schema_file: str) -> bool:
    """
    Check whether the given config file conforms to the given JSON Schema spec and whether any
    filesystem paths it identifies do not exist.
    """
    # Load the config and schema.
    yaml_config = YAMLConfig(config_file)
    yaml_config.dereference_all()
    with open(schema_file, "r", encoding="utf-8") as f:
        schema = json.load(f)
    # Collect and report on schema-validation errors.
    errors = _validation_errors(yaml_config.data, schema)
    log_method = logging.error if errors else logging.info
    log_method("%s schema-validation error%s found", len(errors), "" if len(errors) == 1 else "s")
    for error in errors:
        logging.error(error)
        logging.error("------")
    # It's pointless to evaluate an invalid config, so return now if that's the case.
    if errors:
        return False
    # Collect and report bad paths found in config.
    if bad_paths := _bad_paths(yaml_config.data, schema):
        for bad_path in bad_paths:
            logging.error("Path does not exist: %s", bad_path)
        return False
    # If no issues were detected, report success.
    return True


# Private functions


def _bad_paths(config: dict, schema: dict) -> List[str]:
    """
    Identify non-existent config paths.

    The schema has the same shape as the config, so traverse them together, recursively, checking
    values identified by the schema as having "uri" format, which denotes a path.
    """
    paths = []
    for key, val in config.items():
        subschema = schema["properties"][key]
        if isinstance(val, dict):
            paths += _bad_paths(val, subschema)
        else:
            if subschema.get("format") == "uri" and not Path(val).exists():
                paths.append(val)
    return sorted(paths)


def _validation_errors(config: dict, schema: dict) -> List[str]:
    """
    Identify schema-validation errors.
    """
    validator = jsonschema.Draft7Validator(schema)
    return list(validator.iter_errors(config))
