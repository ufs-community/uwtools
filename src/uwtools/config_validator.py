"""
Support for validating a config using JSON Schema.
"""
import json
from pathlib import Path
from typing import List

import jsonschema

from uwtools.config import YAMLConfig
from uwtools.logger import Logger

# Public


def config_is_valid(config_file: str, schema_file: str, log: Logger) -> bool:
    """
    Check whether the given config file conforms to the given JSON Schema spec and whether any
    filesystem paths it identifies exist.
    """
    yaml_config = YAMLConfig(config_file, log_name=log.name)
    yaml_config.dereference_all()
    with open(schema_file, "r", encoding="utf-8") as f:
        schema = json.load(f)
    if not _config_conforms_to_schema(yaml_config.data, schema, log):
        return False
    if bad_paths := _bad_paths(yaml_config.data, schema, log):
        for bad_path in bad_paths:
            log.error("Path does not exist: %s", bad_path)
        return False
    return True


# Private


def _bad_paths(config: dict, schema: dict, log: Logger) -> List[str]:
    paths = []
    for key, val in config.items():
        subschema = schema["properties"][key]
        if isinstance(val, dict):
            paths += _bad_paths(val, subschema, log)
        else:
            if subschema.get("format") == "uri" and not Path(val).exists():
                paths.append(val)
    return paths


def _config_conforms_to_schema(config: dict, schema: dict, log: Logger) -> bool:
    """
    Does the config object conform to the JSON Schema spec?
    """
    validator = jsonschema.Draft7Validator(schema)
    errors = list(validator.iter_errors(config))
    log_method = log.error if errors else log.info
    log_method("%s schema-validation error%s found", len(errors), "" if len(errors) == 1 else "s")
    for error in errors:
        log.error(error)
        log.error("------")
    return not errors
