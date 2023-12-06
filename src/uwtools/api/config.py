# pylint: disable=unused-import

import os
from typing import Optional, Union

from uwtools.config.atparse_to_jinja2 import convert as _convert_atparse_to_jinja2
from uwtools.config.formats.fieldtable import FieldTableConfig as _FieldTableConfig
from uwtools.config.formats.ini import INIConfig as _INIConfig
from uwtools.config.formats.nml import NMLConfig as _NMLConfig
from uwtools.config.formats.sh import SHConfig as _SHConfig
from uwtools.config.formats.yaml import Config as _Config
from uwtools.config.formats.yaml import YAMLConfig as _YAMLConfig
from uwtools.config.tools import compare_configs as _compare
from uwtools.config.tools import realize_config as _realize
from uwtools.config.validator import validate_yaml as _validate_yaml
from uwtools.types import DefinitePath, OptionalPath
from uwtools.utils.file import FORMAT as _FORMAT

# Public


def compare(
    config_a_path: DefinitePath,
    config_a_format: str,
    config_b_path: DefinitePath,
    config_b_format: str,
) -> bool:
    """
    ???
    """
    return _compare(
        config_a_path=config_a_path,
        config_a_format=config_a_format,
        config_b_path=config_b_path,
        config_b_format=config_b_format,
    )


def get_fieldtable_config(config: Union[dict, OptionalPath] = None) -> _FieldTableConfig:
    """
    Get a FieldTableConfig object.

    :param config: Config file to load (None => read from stdin), or initial dict.
    """
    return _FieldTableConfig(config=config)


def get_ini_config(config: Union[dict, OptionalPath] = None) -> _INIConfig:
    """
    Get a INIConfig object.

    :param config: Config file to load (None => read from stdin), or initial dict.
    """
    return _INIConfig(config=config)


def get_nml_config(config: Union[dict, OptionalPath] = None) -> _NMLConfig:
    """
    Get a NMLConfig object.

    :param config: Config file to load (None => read from stdin), or initial dict.
    """
    return _NMLConfig(config=config)


def get_sh_config(config: Union[dict, OptionalPath] = None) -> _SHConfig:
    """
    Get a SHConfig object.

    :param config: Config file to load (None => read from stdin), or initial dict.
    """
    return _SHConfig(config=config)


def get_yaml_config(config: Union[dict, OptionalPath] = None) -> _YAMLConfig:
    """
    Get a YAMLConfig object.

    :param config: Config file to load (None => read from stdin), or initial dict.
    """
    return _YAMLConfig(config=config)


def realize(
    input_config: Union[dict, _Config, OptionalPath] = None,
    input_format: Optional[str] = None,
    output_file: OptionalPath = None,
    output_format: Optional[str] = None,
    values: Union[dict, _Config, OptionalPath] = None,
    values_format: Optional[str] = None,
    values_needed: bool = False,
    dry_run: bool = False,
) -> bool:
    """
    ???
    """
    _realize(
        input_config=_ensure_config_arg_type(input_config),
        input_format=input_format,
        output_file=output_file,
        output_format=output_format,
        values=_ensure_config_arg_type(values),
        values_format=values_format,
        values_needed=values_needed,
        dry_run=dry_run,
    )
    return True


def realize_to_dict(
    input_config: Union[dict, _Config, OptionalPath] = None,
    input_format: Optional[str] = None,
    values: Union[dict, _Config, OptionalPath] = None,
    values_format: Optional[str] = None,
    values_needed: bool = False,
    dry_run: bool = False,
) -> dict:
    """
    ???
    """
    return _realize(
        input_config=_ensure_config_arg_type(input_config),
        input_format=input_format,
        output_file=os.devnull,
        output_format=None,
        values=_ensure_config_arg_type(values),
        values_format=values_format,
        values_needed=values_needed,
        dry_run=dry_run,
    )


def translate(
    input_file: DefinitePath,
    input_format: str,
    output_file: DefinitePath,
    output_format: str,
    dry_run: bool = False,
) -> bool:
    """
    ???
    """
    if input_format == _FORMAT.atparse and output_format == _FORMAT.jinja2:
        _convert_atparse_to_jinja2(input_file=input_file, output_file=output_file, dry_run=dry_run)
        return True
    return False


def validate(
    schema_file: DefinitePath, config: Optional[Union[dict, _YAMLConfig, OptionalPath]] = None
) -> bool:
    """
    ???
    """
    return _validate_yaml(schema_file=schema_file, config=config)


# Private


def _ensure_config_arg_type(
    config: Union[dict, _Config, OptionalPath]
) -> Union[_Config, OptionalPath]:
    """
    Encapsulate a dict in a Config; return a Config or path argument as-is.

    :param config: A config as a dict, Config, or path.
    """
    if isinstance(config, dict):
        return _YAMLConfig(config=config)
    return config
