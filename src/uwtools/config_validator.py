"""
Support for validating a config using JSON Schema.
"""
import json
from pathlib import Path

import jsonschema

from uwtools.config import YAMLConfig
from uwtools.logger import Logger

# Public


def config_is_valid(config_file: str, validation_schema: str, log: Logger) -> bool:
    """
    Check whether the given config file conforms to the given JSON Schema spec and whether any
    filesystem paths it identifies exist.
    """
    yaml_config = YAMLConfig(config_file, log_name=log.name)
    yaml_config.dereference_all()
    with open(validation_schema, "r", encoding="utf-8") as schema_file:
        schema = json.load(schema_file)
    if not _config_conforms_to_schema(yaml_config.data, schema, log):
        return False
    if not _config_paths_exist(yaml_config.data, schema, log):
        return False
    return True


# Private


def _config_conforms_to_schema(config: dict, schema: dict, log: Logger) -> bool:
    """
    Does the config object conform to the JSON Schema spec?
    """
    validator = jsonschema.Draft7Validator(schema)
    errors = list(validator.iter_errors(config))
    log_method = log.error if errors else log.info
    log_method("Found %s error%s", len(errors), "" if len(errors) == 1 else "s")
    for error in errors:
        log.error(error)
        log.error("------")
    return not errors


def _config_paths_exist(config: dict, schema: dict, log: Logger) -> bool:
    all_ok = True
    for key, val in config.items():
        ok = True
        subschema = schema["properties"][key]
        if isinstance(val, dict):
            ok = _config_paths_exist(val, subschema, log)
        else:
            if subschema.get("format") == "uri":  # denotes a path
                ok = Path(val).exists()
                if not ok:
                    log.error("Path does not exist: %s", val)
        all_ok = all_ok and ok
    return all_ok
