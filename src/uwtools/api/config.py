"""
API access to ``uwtools`` configuration management tools.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING

from uwtools.config.formats.base import Config
from uwtools.config.formats.fieldtable import FieldTableConfig
from uwtools.config.formats.ini import INIConfig
from uwtools.config.formats.nml import NMLConfig
from uwtools.config.formats.sh import SHConfig
from uwtools.config.formats.yaml import YAMLConfig
from uwtools.config.tools import compare as _compare
from uwtools.config.tools import compose as _compose
from uwtools.config.tools import realize as _realize
from uwtools.config.validator import ConfigDataT, ConfigPathT
from uwtools.config.validator import validate_check_config as _validate_check_config
from uwtools.config.validator import validate_external as _validate_external
from uwtools.exceptions import UWConfigError
from uwtools.utils.api import ensure_data_source as _ensure_data_source
from uwtools.utils.file import FORMAT as _FORMAT
from uwtools.utils.file import str2path as _str2path

if TYPE_CHECKING:
    from uwtools.config.support import YAMLKey

# Public


def compare(
    path1: Path | str, path2: Path | str, format1: str | None = None, format2: str | None = None
) -> bool:
    """
    NB: This docstring is dynamically replaced: See compare.__doc__ definition below.
    """
    return _compare(path1=Path(path1), path2=Path(path2), format1=format1, format2=format2)


def compose(
    configs: list[str | Path],
    realize: bool = False,
    output_file: Path | str | None = None,
    input_format: str | None = None,
    output_format: str | None = None,
) -> bool:
    """
    NB: This docstring is dynamically replaced: See compose.__doc__ definition below.
    """
    return _compose(
        configs=list(map(Path, configs)),
        realize=realize,
        output_file=Path(output_file) if output_file else None,
        input_format=input_format,
        output_format=output_format,
    )


def get_fieldtable_config(
    config: dict | Path | str | None = None, stdin_ok: bool = False
) -> FieldTableConfig:
    """
    Get a ``FieldTableConfig`` object.

    :param config: FieldTable file (``None`` => read ``stdin``), or initial ``dict``.
    :param stdin_ok: OK to read from ``stdin``?
    :return: An initialized ``FieldTableConfig`` object.
    """
    return FieldTableConfig(config=_ensure_data_source(_str2path(config), stdin_ok))


def get_ini_config(
    config: dict | Path | str | None = None,
    stdin_ok: bool = False,
) -> INIConfig:
    """
    Get an ``INIConfig`` object.

    :param config: INI file or ``dict`` (``None`` => read ``stdin``).
    :param stdin_ok: OK to read from ``stdin``?
    :return: An initialized ``INIConfig`` object.
    """
    return INIConfig(config=_ensure_data_source(_str2path(config), stdin_ok))


def get_nml_config(
    config: dict | Path | str | None = None,
    stdin_ok: bool = False,
) -> NMLConfig:
    """
    Get an ``NMLConfig`` object.

    :param config: Namelist file of ``dict`` (``None`` => read ``stdin``).
    :param stdin_ok: OK to read from ``stdin``?
    :return: An initialized ``NMLConfig`` object.
    """
    return NMLConfig(config=_ensure_data_source(_str2path(config), stdin_ok))


def get_sh_config(
    config: dict | Path | str | None = None,
    stdin_ok: bool = False,
) -> SHConfig:
    """
    Get an ``SHConfig`` object.

    :param config: Shell key=value pairs file or ``dict`` (``None`` => read ``stdin``).
    :param stdin_ok: OK to read from ``stdin``?
    :return: An initialized ``SHConfig`` object.
    """
    return SHConfig(config=_ensure_data_source(_str2path(config), stdin_ok))


def get_yaml_config(
    config: dict | Path | str | None = None,
    stdin_ok: bool = False,
) -> YAMLConfig:
    """
    Get a ``YAMLConfig`` object.

    :param config: YAML file or ``dict`` (``None`` => read ``stdin``).
    :param stdin_ok: OK to read from ``stdin``?
    :return: An initialized ``YAMLConfig`` object.
    """
    return YAMLConfig(config=_ensure_data_source(_str2path(config), stdin_ok))


def realize(
    input_config: Config | Path | dict | str | None = None,
    input_format: str | None = None,
    update_config: Config | Path | dict | str | None = None,
    update_format: str | None = None,
    output_file: Path | str | None = None,
    output_format: str | None = None,
    key_path: list[YAMLKey] | None = None,
    values_needed: bool = False,
    total: bool = False,
    dry_run: bool = False,
    stdin_ok: bool = False,
) -> dict:
    """
    NB: This docstring is dynamically replaced: See realize.__doc__ definition below.
    """
    if update_config is None and update_format is not None:  # i.e. updates will be read from stdin
        update_config = _ensure_data_source(update_config, stdin_ok)
    return _realize(
        input_config=_ensure_data_source(_str2path(input_config), stdin_ok),
        input_format=input_format,
        update_config=_str2path(update_config),
        update_format=update_format,
        output_file=_str2path(output_file),
        output_format=output_format,
        key_path=key_path,
        values_needed=values_needed,
        total=total,
        dry_run=dry_run,
    )


def realize_to_dict(
    input_config: Config | dict | Path | str | None = None,
    input_format: str | None = None,
    update_config: Config | dict | Path | str | None = None,
    update_format: str | None = None,
    key_path: list[YAMLKey] | None = None,
    values_needed: bool = False,
    total: bool = False,
    dry_run: bool = False,
    stdin_ok: bool = False,
) -> dict:
    """
    Realize a config to a ``dict``, based on a base input config and an optional update config.

    See ``realize()`` for details on arguments, etc.
    """
    return realize(**{**locals(), "output_file": Path(os.devnull), "output_format": _FORMAT.yaml})


def validate(
    schema_file: Path | str,
    config_data: ConfigDataT | None = None,
    config_path: ConfigPathT | None = None,
    stdin_ok: bool = False,
) -> bool:
    """
    Check whether the specified config conforms to the specified JSON Schema spec.

    Specify at most one of config_data or config_path. If no config is specified, ``stdin`` is read
    and will be parsed as YAML and then validated.

    :param schema_file: The JSON Schema file to use for validation.
    :param config_data: A config to validate.
    :param config_path: A path to a file containing a config to validate.
    :param stdin_ok: OK to read from ``stdin``?
    :raises: TypeError if both config_* arguments specified.
    :return: ``True`` if the YAML file conforms to the schema, ``False`` otherwise.
    """
    _validate_check_config(config_data, config_path)
    if config_data is None:
        config_path = _ensure_data_source(_str2path(config_path), stdin_ok)
    try:
        _validate_external(
            schema_file=_str2path(schema_file),
            desc="config",
            config_data=config_data,
            config_path=config_path,
        )
    except UWConfigError:
        return False
    return True


# Import-time code

# The following statements dynamically interpolate values into functions' docstrings, which will not
# work if the docstrings are inlined in the functions. They must remain separate statements to avoid
# hardcoding values into them.

compare.__doc__ = """
Compare two config files.

Recognized file extensions are: {extensions}

:param path1: Path to 1st config file.
:param path2: Path to 2nd config file.
:param format1: Format of 1st config file (optional if file's extension is recognized).
:param format2: Format of 2nd config file (optional if file's extension is recognized).
:return: ``False`` if config files had differences, otherwise ``True``.
""".format(extensions=", ".join([f"``{x}``" for x in _FORMAT.extensions()])).strip()

compose.__doc__ = """
Compose config files.

Specify explicit input or output formats to override default treatment based on file extension.
Recognized file extensions are: {extensions}.

:param configs: Paths to configs to compose.
:param realize: Render template expressions where possible.
:param output_file: Output config destination (default: write to ``stdout``).
:param input_format: Format of configs to compose (choices: {choices}, default: ``{default}``)
:param output_format: Format of output config (choices: {choices}, default: ``{default}``)
:return: ``True`` if no errors were encountered.
""".format(
    default=_FORMAT.yaml,
    extensions=", ".join([f"``{x}``" for x in _FORMAT.extensions()]),
    choices=", ".join([f"``{x}``" for x in (_FORMAT.ini, _FORMAT.nml, _FORMAT.sh, _FORMAT.yaml)]),
).strip()

realize.__doc__ = """
Realize a config based on a base input config and an optional update config.

The input config may be specified as a filesystem path, a ``dict``, or a ``Config`` object. When it
is not, it will be read from ``stdin``.

If an update config is specified, it is merged onto the input config, augmenting or overriding base
values. It may be specified as a filesystem path, a ``dict``, or a ``Config`` object. When it is
not, it will be read from ``stdin``.

At most one of the input config or the update config may be left unspecified, in which case the
other will be read from ``stdin``. If neither filename or format is specified for the update config,
no update will be performed.

The output destination may be specified as a filesystem path. When it is not, it will be written to
``stdout``.

If ``values_needed`` is ``True``, a report of values needed to realize the config is logged. In
``dry_run`` mode, output is written to ``stderr``.

If ``total`` is ``True``, an exception will be raised if any Jinja2 variables/expressions cannot be
rendered. Otherwise, such variables/expressions will be passed through unchanged in the output.

Recognized file extensions are: {extensions}

:param input_config: Input config file (``None`` => read ``stdin``).
:param input_format: Input config format (default: deduced from filename extension; ``yaml`` if that fails).
:param update_config: Update config file (``None`` => read ``stdin``).
:param update_format:  Update config format (default: deduced from filename extension; ``yaml`` if that fails).
:param output_file: Output config file (``None`` => write to ``stdout``).
:param output_format: Output config format (default: deduced from filename extension; ``yaml`` if that fails).
:param key_path: Path of keys to the desired output block.
:param values_needed: Report complete, missing, and template values.
:param total: Require rendering of all Jinja2 variables/expressions.
:param dry_run: Log output instead of writing to output.
:param stdin_ok: OK to read from ``stdin``?
:return: The ``dict`` representation of the realized config.
:raises: ``UWConfigRealizeError`` if ``total`` is ``True`` and any Jinja2 syntax was not rendered.
""".format(extensions=", ".join([f"``{x}``" for x in _FORMAT.extensions()])).strip()  # noqa: E501

__all__ = [
    "Config",
    "FieldTableConfig",
    "INIConfig",
    "NMLConfig",
    "SHConfig",
    "YAMLConfig",
    "compare",
    "compose",
    "get_fieldtable_config",
    "get_ini_config",
    "get_nml_config",
    "get_sh_config",
    "get_yaml_config",
    "realize",
    "realize_to_dict",
    "validate",
]
