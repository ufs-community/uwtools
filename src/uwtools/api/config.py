"""
API access to ``uwtools`` configuration management tools.
"""

import os
from pathlib import Path
from typing import Optional, Union

from uwtools.config.formats.fieldtable import FieldTableConfig as _FieldTableConfig
from uwtools.config.formats.ini import INIConfig as _INIConfig
from uwtools.config.formats.nml import NMLConfig as _NMLConfig
from uwtools.config.formats.sh import SHConfig as _SHConfig
from uwtools.config.formats.yaml import Config as _Config
from uwtools.config.formats.yaml import YAMLConfig as _YAMLConfig
from uwtools.config.tools import compare_configs as _compare
from uwtools.config.tools import realize_config as _realize
from uwtools.config.validator import validate_external as _validate_external
from uwtools.utils.api import ensure_data_source as _ensure_data_source
from uwtools.utils.api import str2path as _str2path
from uwtools.utils.file import FORMAT as _FORMAT

# Public


def compare(
    config_1_path: Union[Path, str],
    config_2_path: Union[Path, str],
    config_1_format: Optional[str] = None,
    config_2_format: Optional[str] = None,
) -> bool:
    """
    NB: This docstring is dynamically replaced: See compare.__doc__ definition below.
    """
    return _compare(
        config_1_path=Path(config_1_path),
        config_2_path=Path(config_2_path),
        config_1_format=config_1_format,
        config_2_format=config_2_format,
    )


def get_fieldtable_config(
    config: Union[dict, Optional[Union[Path, str]]] = None, stdin_ok=False
) -> _FieldTableConfig:
    """
    Get a ``FieldTableConfig`` object.

    :param config: FieldTable file (``None`` => read ``stdin``), or initial ``dict``.
    :param stdin_ok: OK to read from ``stdin``?
    :return: An initialized ``FieldTableConfig`` object.
    """
    return _FieldTableConfig(config=_ensure_data_source(_str2path(config), stdin_ok))


def get_ini_config(
    config: Union[dict, Optional[Union[Path, str]]] = None,
    stdin_ok: bool = False,
) -> _INIConfig:
    """
    Get an ``INIConfig`` object.

    :param config: INI file or ``dict`` (``None`` => read ``stdin``).
    :param stdin_ok: OK to read from ``stdin``?
    :return: An initialized ``INIConfig`` object.
    """
    return _INIConfig(config=_ensure_data_source(_str2path(config), stdin_ok))


def get_nml_config(
    config: Union[dict, Optional[Union[Path, str]]] = None,
    stdin_ok: bool = False,
) -> _NMLConfig:
    """
    Get an ``NMLConfig`` object.

    :param config: Namelist file of ``dict`` (``None`` => read ``stdin``).
    :param stdin_ok: OK to read from ``stdin``?
    :return: An initialized ``NMLConfig`` object.
    """
    return _NMLConfig(config=_ensure_data_source(_str2path(config), stdin_ok))


def get_sh_config(
    config: Union[dict, Optional[Union[Path, str]]] = None,
    stdin_ok: bool = False,
) -> _SHConfig:
    """
    Get an ``SHConfig`` object.

    :param config: Shell key=value pairs file or ``dict`` (``None`` => read ``stdin``).
    :param stdin_ok: OK to read from ``stdin``?
    :return: An initialized ``SHConfig`` object.
    """
    return _SHConfig(config=_ensure_data_source(_str2path(config), stdin_ok))


def get_yaml_config(
    config: Union[dict, Optional[Union[Path, str]]] = None,
    stdin_ok: bool = False,
) -> _YAMLConfig:
    """
    Get a ``YAMLConfig`` object.

    :param config: YAML file or ``dict`` (``None`` => read ``stdin``).
    :param stdin_ok: OK to read from ``stdin``?
    :return: An initialized ``YAMLConfig`` object.
    """
    return _YAMLConfig(config=_ensure_data_source(_str2path(config), stdin_ok))


def realize(
    input_config: Optional[Union[_Config, Path, dict, str]] = None,
    input_format: Optional[str] = None,
    update_config: Optional[Union[_Config, Path, dict, str]] = None,
    update_format: Optional[str] = None,
    output_file: Optional[Union[Path, str]] = None,
    output_format: Optional[str] = None,
    key_path: Optional[list[Union[str, int]]] = None,
    values_needed: bool = False,
    total: bool = False,
    dry_run: bool = False,
    stdin_ok: bool = False,
) -> dict:
    """
    NB: This docstring is dynamically replaced: See realize.__doc__ definition below.
    """
    return _realize(
        input_config=_ensure_data_source(_str2path(input_config), stdin_ok),
        input_format=input_format,
        update_config=_ensure_data_source(_str2path(update_config), stdin_ok),
        update_format=update_format,
        output_file=_str2path(output_file),
        output_format=output_format,
        key_path=key_path,
        values_needed=values_needed,
        total=total,
        dry_run=dry_run,
    )


def realize_to_dict(  # pylint: disable=unused-argument
    input_config: Optional[Union[dict, _Config, Path, str]] = None,
    input_format: Optional[str] = None,
    update_config: Optional[Union[dict, _Config, Path, str]] = None,
    update_format: Optional[str] = None,
    key_path: Optional[list[Union[str, int]]] = None,
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
    schema_file: Union[Path, str],
    config: Optional[Union[dict, _YAMLConfig, Path, str]] = None,
    stdin_ok: bool = False,
) -> bool:
    """
    Check whether the specified config conforms to the specified JSON Schema spec.

    If no config is specified, ``stdin`` is read and will be parsed as YAML and then validated. A
    ``dict`` or a YAMLConfig instance may also be provided for validation.

    :param schema_file: The JSON Schema file to use for validation.
    :param config: The config to validate.
    :param stdin_ok: OK to read from ``stdin``?
    :return: ``True`` if the YAML file conforms to the schema, ``False`` otherwise.
    """
    return _validate_external(
        schema_file=_str2path(schema_file), config=_ensure_data_source(_str2path(config), stdin_ok)
    )


# Import-time code

# The following statements dynamically interpolate values into functions' docstrings, which will not
# work if the docstrings are inlined in the functions. They must remain separate statements to avoid
# hardcoding values into them.

compare.__doc__ = """
Compare two config files.

Recognized file extensions are: {extensions}

:param config_1_path: Path to 1st config file.
:param config_2_path: Path to 2nd config file.
:param config_1_format: Format of 1st config file (optional if file's extension is recognized).
:param config_2_format: Format of 2nd config file (optional if file's extension is recognized).
:return: ``False`` if config files had differences, otherwise ``True``.
""".format(
    extensions=", ".join(_FORMAT.extensions())
).strip()


realize.__doc__ = """
Realize a config based on a base input config and an optional update config.

The input config may be specified as a filesystem path, a ``dict``, or a ``Config`` object. When it
is not, it will be read from ``stdin``.

If an update config is specified, it is merged onto the input config, augmenting or overriding base
values. It may be specified as a filesystem path, a ``dict``, or a ``Config`` object. When it is
not, it will be read from ``stdin``.

At most one of the input config or the update config may be left unspecified, in which case the
other will be read from ``stdin``. If neither filename or format is specified for the update config, no
update will be performed.

The output destination may be specified as a filesystem path. When it is not, it will be written to
``stdout``.

If ``values_needed`` is ``True``, a report of values needed to realize the config is logged. In
``dry_run`` mode, output is written to ``stderr``.

If ``total`` is ``True``, an exception will be raised if any Jinja2 variables/expressions cannot be
rendered. Otherwise, such variables/expressions will be passed through unchanged in the output.

Recognized file extensions are: {extensions}

:param input_config: Input config file (``None`` => read ``stdin``).
:param input_format: Format of the input config (optional if file's extension is recognized).
:param update_config: Update config file (``None`` => read ``stdin``).
:param update_format: Format of the update config (optional if file's extension is recognized).
:param output_file: Output config file (``None`` => write to ``stdout``).
:param output_format: Format of the output config (optional if file's extension is recognized).
:param key_path: Path through keys to the desired output block.
:param values_needed: Report complete, missing, and template values.
:param total: Require rendering of all Jinja2 variables/expressions.
:param dry_run: Log output instead of writing to output.
:param stdin_ok: OK to read from ``stdin``?
:return: The ``dict`` representation of the realized config.
:raises: UWConfigRealizeError if ``total`` is ``True`` and any Jinja2 variable/expression was not rendered.
""".format(
    extensions=", ".join(_FORMAT.extensions())
).strip()
