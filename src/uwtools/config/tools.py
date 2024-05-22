"""
Tools for working with configs.
"""

from pathlib import Path
from typing import Callable, List, Optional, Tuple, Union

from uwtools.config.formats.base import Config
from uwtools.config.jinja2 import unrendered
from uwtools.config.support import depth, format_to_config, log_and_error
from uwtools.exceptions import UWConfigError, UWConfigRealizeError, UWError
from uwtools.logging import MSGWIDTH, log
from uwtools.strings import FORMAT
from uwtools.utils.file import get_file_format

# Public functions


def compare_configs(
    config_1_path: Path,
    config_2_path: Path,
    config_1_format: Optional[str] = None,
    config_2_format: Optional[str] = None,
) -> bool:
    """
    NB: This docstring is dynamically replaced: See compare_configs.__doc__ definition below.
    """
    config_1_format = _ensure_format("1st config file", config_1_format, config_1_path)
    config_2_format = _ensure_format("2nd config file", config_2_format, config_2_path)
    if config_1_format != config_2_format:
        log.error("Formats do not match: %s vs %s", config_1_format, config_2_format)
        return False
    cfg_1: Config = format_to_config(config_1_format)(config_1_path)
    cfg_2: Config = format_to_config(config_2_format)(config_2_path)
    log.info("- %s", config_1_path)
    log.info("+ %s", config_2_path)
    log.info("-" * MSGWIDTH)
    return cfg_1.compare_config(cfg_2.data)


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
    input_config: Union[Config, Optional[Path]] = None,
    input_format: Optional[str] = None,
    update_config: Union[Config, Optional[Path]] = None,
    update_format: Optional[str] = None,
    output_file: Optional[Path] = None,
    output_format: Optional[str] = None,
    output_block: Optional[List[Union[str, int]]] = None,
    values_needed: bool = False,
    total: bool = False,
    dry_run: bool = False,
) -> dict:
    """
    NB: This docstring is dynamically replaced: See realize_config.__doc__ definition below.
    """
    input_obj, input_format = _realize_config_input_setup(input_config, input_format)
    input_obj = _realize_config_update(input_obj, update_config, update_format)
    input_obj.dereference()
    output_data, output_format = _realize_config_output_setup(
        input_obj, output_file, output_format, output_block
    )
    if dry_run:
        for line in str(input_obj).strip().split("\n"):
            log.info(line)
        return {}
    if values_needed:
        _realize_config_values_needed(input_obj)
        return {}
    if total and unrendered(str(input_obj)):
        raise UWConfigRealizeError("Config could not be totally realized")
    output_class = format_to_config(output_format)
    output_class.dump_dict(cfg=output_data, path=output_file)
    return input_obj.data


# Private functions


def _ensure_format(
    desc: str, fmt: Optional[str] = None, config: Union[Config, Optional[Path]] = None
) -> str:
    """
    Return the given format, or the appropriate format as deduced from the config.

    :param desc: A description of the file.
    :param fmt: The config format name.
    :param config: The input config.
    :return: The specified or deduced format.
    :raises: UWError if the format cannot be determined.
    """
    if isinstance(config, Config):
        return config.get_format()
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


def _realize_config_input_setup(
    input_config: Union[Config, Optional[Path]] = None, input_format: Optional[str] = None
) -> Tuple[Config, str]:
    """
    Set up config-realize input.

    :param input_config: Input config source (None => read stdin).
    :param input_format: Format of the input config.
    :return: The input Config object and its format name.
    """
    input_format = _ensure_format("input", input_format, input_config)
    if not input_config:
        log.debug("Reading input from stdin")
    input_obj: Config = (
        input_config
        if isinstance(input_config, Config)
        else format_to_config(input_format)(config=input_config)
    )
    return input_obj, input_format


def _realize_config_output_setup(
    input_obj: Config,
    output_file: Optional[Path] = None,
    output_format: Optional[str] = None,
    output_block: Optional[List[Union[str, int]]] = None,
) -> Tuple[dict, str]:
    """
    Set up config-realize output.

    :param input_obj: The input Config object.
    :param output_file: Output config destination (None => write to stdout).
    :param output_format: Format of the output config.
    :param output_block: Path through keys to the desired output block.
    :return: The unrealized data to output and the output format name.
    """
    output_format = _ensure_format("output", output_format, output_file)
    log.debug("Writing output to %s" % (output_file or "stdout"))
    _validate_format("output", output_format, input_obj.get_format())
    output_data = input_obj.data
    if output_block is not None:
        for key in output_block:
            output_data = output_data[key]
    config_check_depths_realize(output_data, output_format)
    return output_data, output_format


def _realize_config_update(
    input_obj: Config,
    update_config: Union[Config, Optional[Path]] = None,
    update_format: Optional[str] = None,
) -> Config:
    """
    Set up config-realize update.

    :param input_obj: The input Config object.
    :param update_config: Input config source (None => read stdin).
    :param update_format: Format of the update config.
    :return: The updated but unrealized Config object.
    """
    if update_config or update_format:
        update_format = _ensure_format("update", update_format, update_config)
        if not update_config:
            log.debug("Reading update from stdin")
        _validate_format("update", update_format, input_obj.get_format())
        update_obj: Config = (
            update_config
            if isinstance(update_config, Config)
            else format_to_config(update_format)(config=update_config)
        )
        log.debug("Initial input config depth: %s", input_obj.depth)
        log.debug("Update config depth: %s", update_obj.depth)
        config_check_depths_update(update_obj, input_obj.get_format())
        input_obj.update_values(update_obj)
        log.debug("Final input config depth: %s", input_obj.depth)
    return input_obj


def _realize_config_values_needed(input_obj: Config) -> bool:
    """
    Print a report characterizing input values as complete, empty, or template placeholders.

    :param input_obj: The config to update.
    :return: True
    """
    complete, empty, template = input_obj.characterize_values(input_obj.data, parent="")
    if complete:
        log.info("Keys that are complete:")
        for var in complete:
            log.info(var)
    else:
        log.info("No keys are complete.")
    log.info("")
    if template:
        log.info("Keys with unrendered Jinja2 variables/expressions:")
        for var in template:
            log.info(var)
    else:
        log.info("No keys have unrendered Jinja2 variables/expressions.")
    log.info("")
    if empty:
        log.info("Keys that are set to empty:")
        for var in empty:
            log.info(var)
    else:
        log.info("No keys are set to empty.")
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
        raise UWConfigError(
            "Cannot %s depth-%s config to type-'%s' config" % (action, depth(config), target_format)
        )


def _validate_format(other_fmt_desc: str, other_fmt: str, input_fmt: str) -> None:
    """
    Ensure a format agrees with the input format.

    :param other_fmt_desc: Description of other format.
    :param other_fmt: Other format.
    :param input_fmt: Input format.
    :raises: UWError if other format is incompatible.
    """
    if FORMAT.yaml not in (input_fmt, other_fmt) and input_fmt != other_fmt:
        raise UWError(
            "Accepted %s formats for input format %s are %s or %s"
            % (other_fmt_desc, input_fmt, input_fmt, FORMAT.yaml)
        )


# Import-time code

# The following statements dynamically interpolate values into functions' docstrings, which will not
# work if the docstrings are inlined in the functions. They must remain separate statements to avoid
# hardcoding values into them.

compare_configs.__doc__ = """
Compare two config files.

Recognized file extensions are: {extensions}

:param config_1_path: Path to 1st config file
:param config_2_path: Path to 2nd config file
:param config_1_format: Format of 1st config file (optional if file's extension is recognized)
:param config_2_format: Format of 2nd config file (optional if file's extension is recognized)
:return: ``False`` if config files had differences, otherwise ``True``
""".format(
    extensions=", ".join(FORMAT.extensions())
).strip()


realize_config.__doc__ = """
Realize an output config based on an input config and optional values-providing configs.

Recognized file extensions are: {extensions}

:param input_config: Input config source (None => read ``stdin``).
:param input_format: Format of the input config.
:param update_config: Input config source (None => read ``stdin``).
:param update_format: Format of the update config.
:param output_file: Output config destination (None => write to ``stdout``).
:param output_format: Format of the output config.
:param output_block: Path through keys to the desired output block.
:param values_needed: Report complete, missing, and template values.
:param total: Require rendering of all Jinja2 variables/expressions.
:param dry_run: Log output instead of writing to output.
:raises: UWConfigRealizeError if ``total`` is ``True`` and config cannot be totally realized.
:return: The realized config (or an empty-dict for no-op modes).
""".format(
    extensions=", ".join(FORMAT.extensions())
).strip()
