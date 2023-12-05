# pylint: disable=unused-import

from typing import Optional, Union

from uwtools.config.atparse_to_jinja2 import convert as _convert_atparse_to_jinja2
from uwtools.config.formats.yaml import Config as _Config
from uwtools.config.formats.yaml import YAMLConfig as _YAMLConfig
from uwtools.config.tools import compare_configs as _compare
from uwtools.config.tools import realize_config as _realize
from uwtools.config.validator import validate_yaml_config as _validate_yaml_config
from uwtools.config.validator import validate_yaml_file as _validate_yaml_file
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
    return _realize(
        input_config=_ensure_config_arg_type(input_config),
        input_format=input_format,
        output_file=output_file,
        output_format=output_format,
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
    schema_file: DefinitePath, config: Optional[Union[dict, _Config, OptionalPath]] = None
) -> bool:
    """
    ???
    """
    if isinstance(config, dict):
        cfgobj = _YAMLConfig(empty=True)
        cfgobj.update(config)
        return _validate_yaml_config(schema_file=schema_file, config=cfgobj)
    if isinstance(config, _Config):
        return validate(schema_file=schema_file, config=config.data)
    return _validate_yaml_file(schema_file=schema_file, config_file=config)


# Private


def _ensure_config_arg_type(
    config: Union[dict, _Config, OptionalPath]
) -> Union[_Config, OptionalPath]:
    """
    ???
    """
    if isinstance(config, dict):
        cfgobj = _YAMLConfig(empty=True)
        cfgobj.update(config)
        return cfgobj
    return config
