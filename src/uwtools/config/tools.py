"""
Tools for working with configs.
"""

from __future__ import annotations

import os
from functools import reduce
from pathlib import Path
from tempfile import mkstemp
from textwrap import indent
from typing import cast
from uuid import uuid4

from yaml.composer import ComposerError

from uwtools.config.formats.base import Config
from uwtools.config.formats.yaml import YAMLConfig
from uwtools.config.jinja2 import unrendered
from uwtools.config.support import YAMLKey, depth, format_to_config, log_and_error
from uwtools.exceptions import UWConfigError, UWConfigRealizeError, UWError
from uwtools.logging import log
from uwtools.strings import FORMAT
from uwtools.utils.file import get_config_format

# Public functions


def compare(
    path1: Path, path2: Path, format1: str | None = None, format2: str | None = None
) -> bool:
    """
    NB: This docstring is dynamically replaced: See compare.__doc__ definition below.
    """
    format1 = _ensure_format("1st config file", format1, path1)
    format2 = _ensure_format("2nd config file", format2, path2)
    if format1 != format2:
        log.error("Formats do not match: %s vs %s", format1, format2)
        return False
    cfg_1: Config = format_to_config(format1)(path1)
    cfg_2: Config = format_to_config(format2)(path2)
    log.info("- %s", path1)
    log.info("+ %s", path2)
    return cfg_1.compare_config(cfg_2.as_dict())


def compose(
    configs: list[Path],
    realize: bool,
    output_file: Path | None = None,
    input_format: str | None = None,
    output_format: str | None = None,
) -> bool:
    """
    NB: This docstring is dynamically replaced: See compose.__doc__ definition below.
    """

    def cfgobj_from_yaml(yaml: str) -> YAMLConfig:
        """
        Write YAML to a temp file, instantiate a config from it, then clean up.

        :param yaml: The YAML string from which to instantiate the config.
        :return: A YAMLConfig object.
        """
        tmp_fd, tmp_name = mkstemp(text=True)
        os.close(tmp_fd)
        tmp = Path(tmp_name)
        tmp.write_text(yaml)
        new = YAMLConfig(tmp)
        tmp.unlink()
        return new

    def cfgobj_get(path: Path) -> Config:
        """
        Get a Config object representing the data in the specified file.

        If instantiation fails due to an undefined YAML alias, build in-memory YAML combining the
        bad YAML with that of each subsequent to-be-composed file, expecting that one of the latter
        defines the missing anchor. Nest the other-file YAML blocks under unique top-level keys to
        avoid conflicts. After successful instantiation, remove the added key-value pairs. Note that
        this procedure applies only to YAML configs.

        :param path: Path to the config file.
        :return: An instance of the subclass of Config appropriate to the format of the config.
        """
        try:
            return input_class(path)
        except ComposerError as e:
            if not (e.problem and "found undefined alias" in e.problem):
                raise
            yaml = path.read_text().strip()
            keys = []
            for config in configs[configs.index(path) + 1 :]:
                while (key := uuid4().hex) in yaml:
                    ...
                keys.append(key)
                other = indent(config.read_text().strip(), prefix="  ")
                yaml = "\n".join([f"{key}:", other, yaml])
            cfgobj = cfgobj_from_yaml(yaml)
            for key in keys:
                del cfgobj[key]
            return cfgobj

    def cfgobj_update(config: Config, path: Path) -> Config:
        """
        Update the given Config object with config data from the given file.

        :param config: The Config objet to update.
        :param path: Path to the file containing config data to update with.
        :return: And updated Config object.
        """
        log.debug("Composing '%s' config from %s", input_format, path)
        config.update_from(cfgobj_get(path))
        return config

    input_format = input_format or get_config_format(configs[0], "input")
    input_class: type[Config] = format_to_config(input_format)
    config = reduce(cfgobj_update, configs[1:], cfgobj_get(configs[0]))
    output_format = output_format or get_config_format(output_file, "output")
    output_class = format_to_config(output_format)
    output_config = output_class(config)
    if realize:
        output_config.dereference()
    output_config.dump(output_file)
    return True


def realize(
    input_config: Config | Path | dict | None = None,
    input_format: str | None = None,
    update_config: Config | Path | dict | None = None,
    update_format: str | None = None,
    output_file: Path | None = None,
    output_format: str | None = None,
    key_path: list[YAMLKey] | None = None,
    values_needed: bool = False,
    total: bool = False,
    dry_run: bool = False,
) -> dict:
    """
    NB: This docstring is dynamically replaced: See realize.__doc__ definition below.
    """
    input_obj = _realize_input_setup(input_config, input_format)
    input_obj = _realize_update(input_obj, update_config, update_format)
    input_obj.dereference()
    output_data, output_format = _realize_output_setup(
        input_obj, output_file, output_format, key_path
    )
    if dry_run:
        for line in str(input_obj).strip().split("\n"):
            log.info(line)
        return {}
    if values_needed:
        _realize_values_needed(input_obj)
        return {}
    if total and unrendered(str(input_obj)):
        msg = "Config could not be totally realized"
        raise UWConfigRealizeError(msg)
    output_class = cast(Config, format_to_config(output_format))
    output_class.dump_dict(cfg=output_data, path=output_file)
    return input_obj.data


def validate_depth(config_obj: Config | dict, target_format: str) -> None:
    """
    :param config_obj: The reference config object.
    :param target_format: The target format.
    :raises: UWConfigError on excessive config object depth.
    """
    target_class = cast(Config, format_to_config(target_format))
    config = config_obj.data if isinstance(config_obj, Config) else config_obj
    if not target_class._depth_ok(depth(config)):  # noqa: SLF001
        msg = "Cannot treat depth-%s config as '%s'" % (depth(config), target_format)
        raise UWConfigError(msg)


def walk_key_path(config: dict, key_path: list[YAMLKey]) -> tuple[dict, str]:
    """
    Navigate to the sub-config at the end of the path of given keys.

    :param config: A config.
    :param key_path: Path of keys to config block to use.
    :return: The sub-config and a string representation of the key path.
    """
    keys = []
    pathstr = "<unknown>"
    for key in key_path:
        keys.append(key)
        pathstr = ".".join(str(key) for key in keys)
        try:
            subconfig = config[key]
        except KeyError as e:
            msg = f"Bad config path: {pathstr}"
            raise log_and_error(msg) from e
        if not isinstance(subconfig, dict):
            msg = f"Value at {pathstr} must be a dictionary"
            raise log_and_error(msg)
        config = subconfig
    return config, pathstr


# Private functions


def _ensure_format(
    desc: str, fmt: str | None = None, config: Config | Path | dict | None = None
) -> str:
    """
    Return the given format, or the deduced format.

    :param desc: A description of the file.
    :param fmt: The config format name.
    :param config: The input config.
    :return: The specified or deduced format.
    """
    if fmt:
        return fmt
    if isinstance(config, Config):
        return config._get_format()  # noqa: SLF001
    if isinstance(config, dict):
        return FORMAT.yaml
    return get_config_format(config, desc)


def _realize_input_setup(
    input_config: Config | Path | dict | None = None, input_format: str | None = None
) -> Config:
    """
    Set up config-realize input.

    :param input_config: Input config source (None => read from stdin).
    :param input_format: Format of the input config.
    :return: The input Config object.
    """
    if isinstance(input_config, Config):
        return input_config
    input_format = _ensure_format("input", input_format, input_config)
    if not input_config:
        log.debug("Reading input from stdin")
    config_obj: Config = format_to_config(input_format)(config=input_config)
    return config_obj


def _realize_output_setup(
    input_obj: Config,
    output_file: Path | None = None,
    output_format: str | None = None,
    key_path: list[YAMLKey] | None = None,
) -> tuple[dict, str]:
    """
    Set up config-realize output.

    :param input_obj: The input Config object.
    :param output_file: Output config destination (None => write to stdout).
    :param output_format: Format of the output config.
    :param key_path: Path of keys to config block to use.
    :return: The unrealized data to output and the output format name.
    """
    output_format = _ensure_format("output", output_format, output_file)
    log.debug("Writing output to %s", output_file or "stdout")
    fmt = input_obj._get_format()  # noqa: SLF001
    _validate_format("output", output_format, fmt)
    output_data = input_obj.data
    if key_path is not None:
        for key in key_path:
            output_data = output_data[key]
    validate_depth(output_data, output_format)
    return output_data, output_format


def _realize_update(
    input_obj: Config,
    update_config: Config | Path | dict | None = None,
    update_format: str | None = None,
) -> Config:
    """
    Set up config-realize update.

    :param input_obj: The input Config object.
    :param update_config: Input config source (None => read from stdin).
    :param update_format: Format of the update config.
    :return: The updated but unrealized Config object.
    """
    if update_config or update_format:
        update_format = _ensure_format("update", update_format, update_config)
        fmt = lambda x: x._get_format()  # noqa: SLF001
        depth_ = lambda x: x._depth  # noqa: SLF001
        if not update_config:
            log.debug("Reading update from stdin")
        _validate_format("update", update_format, fmt(input_obj))
        update_obj: Config = (
            update_config
            if isinstance(update_config, Config)
            else format_to_config(update_format)(config=update_config)
        )
        log.debug("Initial input config depth: %s", depth_(input_obj))
        log.debug("Update config depth: %s", depth_(update_obj))
        validate_depth(update_obj, fmt(input_obj))
        input_obj.update_from(update_obj)
        log.debug("Final input config depth: %s", depth_(input_obj))
    return input_obj


def _realize_values_needed(input_obj: Config) -> None:
    """
    Print a report characterizing input values as complete, empty, or template placeholders.

    :param input_obj: The config to update.
    """
    complete, template = input_obj._characterize_values(  # noqa: SLF001
        input_obj.data, parent=""
    )
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


def _validate_format(other_fmt_desc: str, other_fmt: str, input_fmt: str) -> None:
    """
    Ensure a format agrees with the input format.

    :param other_fmt_desc: Description of other format.
    :param other_fmt: Other format.
    :param input_fmt: Input format.
    :raises: UWError if other format is incompatible.
    """
    if FORMAT.yaml not in (input_fmt, other_fmt) and input_fmt != other_fmt:
        msg = "Accepted %s formats for input format %s are %s or %s" % (
            other_fmt_desc,
            input_fmt,
            input_fmt,
            FORMAT.yaml,
        )
        raise UWError(msg)


# Import-time code

# The following statements dynamically interpolate values into functions' docstrings, which will not
# work if the docstrings are inlined in the functions. They must remain separate statements to avoid
# hardcoding values into them.

compare.__doc__ = """
Compare two config files.

Recognized file extensions are: {extensions}

:param path1: Path to 1st config file
:param path2: Path to 2nd config file
:param format1: Format of 1st config file (optional if file's extension is recognized)
:param format2: Format of 2nd config file (optional if file's extension is recognized)
:return: False if config files had differences, otherwise True
""".format(extensions=", ".join(FORMAT.extensions())).strip()

compose.__doc__ = """
Compose config files.

Recognized file extensions are: {extensions}

:param configs: Paths to configs to compose.
:param output_file: Output config destination (default: write to stdout).
:param input_format: Format of configs to compose (choices: {choices}, default: {default}).
:param output_format: Format of output config (choices: {choices}, default: {default}).
:return: True if no errors were encountered.
""".format(
    default=FORMAT.yaml,
    extensions=", ".join(FORMAT.extensions()),
    choices=", ".join([FORMAT.ini, FORMAT.nml, FORMAT.sh, FORMAT.yaml]),
).strip()

realize.__doc__ = """
Realize an output config based on an input config and optional values-providing configs.

Recognized file extensions are: {extensions}

:param input_config: Input config source (None => read from stdin).
:param input_format: Input config format.
:param update_config: Input config source (None => read from stdin).
:param update_format: Update config format.
:param output_file: Output config destination (None => write to stdout).
:param output_format: Output config format.
:param key_path: Path of keys to the desired output block.
:param values_needed: Report complete, missing, and template values.
:param total: Require rendering of all Jinja2 variables/expressions.
:param dry_run: Log output instead of writing to output.
:raises: UWConfigRealizeError if total is True and config cannot be totally realized.
:return: The realized config (or an empty-dict for no-op modes).
""".format(extensions=", ".join(FORMAT.extensions())).strip()
