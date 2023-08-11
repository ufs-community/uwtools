"""
Support for validating a config using JSON Schema.
"""
import json

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
    return True


# Private


def _config_conforms_to_schema(config: dict, schema: dict, log: Logger) -> bool:
    """
    Check whether the config object conforms to the JSON Schema spec.
    """
    validator = jsonschema.Draft7Validator(schema)
    errors = list(validator.iter_errors(config))
    log_method = log.error if errors else log.info
    log_method("Found %s error%s", len(errors), "" if len(errors) == 1 else "s")
    for error in errors:
        log.error(error)
        log.error("------")
    return not errors


# def _config_paths_exist(config: dict, schema: dict) -> bool:
#     for key, val in config.items():

#     return True
#     # Create a list of fields that could contain a file or path.

#     path_list = []
#     for field in schema["properties"]:
#         for value in schema["properties"][field]["properties"]:
#             # the json pair "format": "uri" labels a path or file
#             if "format" in schema["properties"][field]["properties"][value]:
#                 path_list.append(value)

#     # Check for existence of those files or paths.

#     for field in config_obj.data:
#         for value in config_obj.data[field]:
#             if value in path_list:
#                 if not os.path.exists(config_obj.data[field][value]):
#                     schema_error += 1
#                     log.error("%s has Invalid Path %s", value, config_obj.data[field][value])
