"""
Tools for working with configs.
"""

from typing import Callable, List, Optional, Union

from uwtools.config.formats.base import Config
from uwtools.config.formats.yaml import YAMLConfig
from uwtools.config.support import depth, format_to_config, log_and_error
from uwtools.exceptions import UWError
from uwtools.logging import MSGWIDTH, log
from uwtools.types import DefinitePath, OptionalPath
from uwtools.utils.file import FORMAT, get_file_format

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


def config_check_depths_dump(config_obj: Union[Config, dict], target_format: str) -> None:
    """
    Check that the depth does not exceed the target format's max.

    :param config_obj: The reference config dictionary.
    :param target_format: The target format.
    :raises: UWConfigError on excessive config object dictionary depth.
    """
    # Define a function with the conditions of an invalid depth.
    bad_depth = lambda need, have: need and have > need
    _validate_depth(config_obj, target_format, "dump", bad_depth)


def config_check_depths_realize(config_obj: Union[Config, dict], target_format: str) -> None:
    """
    Check that the depth does not exceed the target format's max.

    :param config_obj: The reference config object.
    :param target_format: The target format.
    """
    # Define a function with the conditions of an invalid depth.
    bad_depth = lambda need, have: need and have != need
    _validate_depth(config_obj, target_format, "realize", bad_depth)


def config_check_depths_update(config_obj: Union[Config, dict], target_format: str) -> None:
    """
    Check that the depth does not exceed the target format's max.

    :param config_obj: The reference config object.
    :param target_format: The target format.
    """
    # Define a function with the conditions of an invalid depth.
    bad_depth = lambda need, have: need and have > need
    _validate_depth(config_obj, target_format, "update", bad_depth)


def realize_config(
    input_config: Union[Config, OptionalPath] = None,
    input_format: Optional[str] = None,
    output_file: OptionalPath = None,
    output_format: Optional[str] = None,
    supplemental_configs: Optional[List[Union[dict, Config, DefinitePath]]] = None,
    values_needed: bool = False,
    dry_run: bool = False,
) -> dict:
    """
    Realize an output config based on an input config and optional values-providing configs.

    :param input_config: Input config file (None => read stdin).
    :param input_format: Format of the input config.
    :param output_file: Output config file (None => write to stdout).
    :param output_format: Format of the output config.
    :param supplemental_configs: Sources of values used to modify input.
    :param values_needed: Report complete, missing, and template values.
    :param dry_run: Log output instead of writing to output.
    :return: The realized config (or an empty-dict for no-op modes).
    """
    input_format = _ensure_format("input", input_format, input_config)
    input_obj = (
        input_config
        if isinstance(input_config, Config)
        else format_to_config(input_format)(config=input_config)
    )
    if supplemental_configs:
        input_obj = _realize_config_update(input_obj, supplemental_configs)
        input_obj.dereference()
    output_format = _ensure_format("output", output_format, output_file)
    config_check_depths_realize(input_obj, output_format)
    if dry_run:
        log.info(input_obj)
        return {}
    if values_needed:
        _realize_config_values_needed(input_obj)
        return {}
    output_obj = format_to_config(output_format)
    output_obj.dump_dict(path=output_file, cfg=input_obj.data)
    return input_obj.data


# Private functions


def _ensure_format(
    desc: str, fmt: Optional[str] = None, config: Union[Config, OptionalPath] = None
) -> str:
    """
    Return the given file format, or the appropriate format as deduced from the config.

    :param desc: A description of the file.
    :param fmt: The config format name.
    :param config: The input config.
    :return: The specified or deduced format.
    :raises: UWError if the format cannot be determined.
    """
    if isinstance(config, Config):
        return FORMAT.yaml
    if fmt is None:
        if config is not None:
            fmt = get_file_format(config)
        else:
            raise UWError(f"Either {desc} file format or name must be specified")
    return fmt


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


def _realize_config_update(
    config_obj: Config,
    supplemental_configs: Optional[List[Union[dict, Config, DefinitePath]]] = None,
) -> Config:
    """
    Update config with values from other configs, if given.

    :param config_obj: The config to update.
    :param supplemental_configs: Sources of values to modify input.
    :return: The input config, possibly updated.
    """
    if supplemental_configs:
        log.debug("Before update, config has depth %s", config_obj.depth)
        supplemental_obj: Config
        for config in supplemental_configs:
            if isinstance(config, dict):
                supplemental_obj = YAMLConfig(config=config)
            elif isinstance(config, Config):
                supplemental_obj = config
            else:
                supplemental_format = get_file_format(config)
                supplemental_obj = format_to_config(supplemental_format)(config=config)
            log.debug("Supplemental config has depth %s", supplemental_obj.depth)
            config_check_depths_update(supplemental_obj, config_obj.get_format())
            config_obj.update_values(supplemental_obj)
            log.debug("After update, config has depth %s", config_obj.depth)
    else:
        log.debug("Input config has depth %s", config_obj.depth)
    return config_obj


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


def _validate_depth(
    config_obj: Union[Config, dict], target_format: str, action: str, bad_depth: Callable
) -> None:
    """
    :param config_obj: The reference config object.
    :param target_format: The target format.
    :param action: The action being performed.
    :param bad_depth: A function that returns True if the depth is bad.
    :raises: UWConfigError on excessive config object depth.
    """
    target_class = format_to_config(target_format)
    config = config_obj.data if isinstance(config_obj, Config) else config_obj
    if bad_depth(target_class.get_depth_threshold(), depth(config)):
        raise log_and_error(
            "Cannot %s depth-%s config to type-'%s' config" % (action, depth(config), target_format)
        )
