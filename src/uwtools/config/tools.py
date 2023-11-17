"""
Tools for working with configs.
"""

from typing import List, Optional

from uwtools.config.formats.base import Config
from uwtools.config.support import format_to_config, log_and_error
from uwtools.exceptions import UWConfigError
from uwtools.logging import MSGWIDTH, log
from uwtools.types import DefinitePath, OptionalPath
from uwtools.utils.file import FORMAT, get_file_type

# Public functions


def compare_configs(
    config_a_path: DefinitePath,
    config_a_format: str,
    config_b_path: DefinitePath,
    config_b_format: str,
) -> bool:
    """
    Compare two config files.

    :param config_a_path: Path to first config file.
    :param config_a_format: Format of first config file.
    :param config_b_path: Path to second config file.
    :param config_b_format: Format of second config file.
    :return: False if config files had differences, otherwise True.
    """

    cfg_a = format_to_config(config_a_format)(config_a_path)
    cfg_b = format_to_config(config_b_format)(config_b_path)
    log.info("- %s", config_a_path)
    log.info("+ %s", config_b_path)
    log.info("-" * MSGWIDTH)
    return cfg_a.compare_config(cfg_b.data)


def realize_config(
    input_file: OptionalPath,
    input_format: str,
    output_file: OptionalPath,
    output_format: str,
    values_file: OptionalPath,
    values_format: Optional[str],
    values_needed: bool = False,
    dry_run: bool = False,
) -> bool:
    """
    Realize an output config based on an input config and an optional values-providing config.

    :param input_file: Input config file (stdin used when None).
    :param input_format: Format of the input config.
    :param output_file: Output config file (stdout used when None).
    :param output_format: Format of the output config.
    :param values_file: File providing values to modify input.
    :param values_format: Format of the values config file.
    :param values_needed: Provide a report about complete, missing, and template values.
    :param dry_run: Log output instead of writing to output.
    :return: True if no exception is raised.
    :raises: UWConfigError if errors are encountered.
    """

    input_obj = format_to_config(input_format)(config_file=input_file)
    input_obj.dereference()
    input_obj = _realize_config_update(input_obj, values_file, values_format)
    _realize_config_check_depths(input_obj, output_format)
    if values_needed:
        return _realize_config_values_needed(input_obj)
    if dry_run:
        log.info(input_obj)
    else:
        format_to_config(output_format).dump_dict(path=output_file, cfg=input_obj.data)
    return True


# Private functions


def _print_config_section(config: dict, key_path: List[str]) -> None:
    """
    Descends into the config via the given keys, then prints the contents of the located subtree as
    key=value pairs, one per line.
    """
    keys = []
    current_path = "<unknown>"
    for section in key_path:
        keys.append(section)
        current_path = " -> ".join(keys)
        try:
            subconfig = config[section]
        except KeyError as e:
            raise log_and_error(f"Bad config path: {current_path}") from e
        if not isinstance(subconfig, dict):
            raise log_and_error(f"Value at {current_path} must be a dictionary")
        config = subconfig
    output_lines = []
    for key, value in config.items():
        if type(value) not in (bool, float, int, str):
            raise log_and_error(f"Non-scalar value {value} found at {current_path}")
        output_lines.append(f"{key}={value}")
    print("\n".join(sorted(output_lines)))


def _realize_config_check_depths(input_obj: Config, output_format: str) -> None:
    """
    Check that the depth of the input config does not exceed the output format's max.

    :param input_obj: The input config.
    :param output_format: The output format:
    :raises: UWConfigError on excessive input-config depth.
    """
    if (output_format == FORMAT.ini and input_obj.depth > 2) or (
        output_format == FORMAT.nml and input_obj.depth != 2
    ):
        msg = "Cannot write depth-%s input to type-'%s' output" % (input_obj.depth, output_format)
        log.error(msg)
        raise UWConfigError(msg)


def _realize_config_update(
    input_obj: Config, values_file: OptionalPath, values_format: Optional[str]
) -> Config:
    """
    Update config with values from another config, if given.

    :param input_obj: The config to update.
    :param values_file: File providing values to modify input.
    :param values_format: Format of the values config file.
    :return: The input config, possibly updated.
    """
    if values_file:
        log.debug("Before update, config has depth %s", input_obj.depth)
        values_format = values_format or get_file_type(values_file)
        values_obj = format_to_config(values_format)(config_file=values_file)
        log.debug("Values config has depth %s", values_obj.depth)
        input_obj.update_values(values_obj)
        input_obj.dereference()
        log.debug("After update, input config has depth %s", input_obj.depth)
    else:
        log.debug("Input config has depth %s", input_obj.depth)
    return input_obj


def _realize_config_values_needed(input_obj: Config) -> bool:
    """
    Print a report characterizing input values as complete, empty, or template placeholders.

    :param input_obj: The config to update.
    """
    complete, empty, template = input_obj.characterize_values(input_obj.data, parent="")
    log.info("Keys that are complete:")
    for var in complete:
        log.info(var)
    log.info("")
    log.info("Keys that have unfilled Jinja2 templates:")
    for var in template:
        log.info(var)
    log.info("")
    log.info("Keys that are set to empty:")
    for var in empty:
        log.info(var)
    return True
