# pylint: disable=unused-import

from tempfile import NamedTemporaryFile
from typing import Optional, Union

import yaml

from uwtools.config.atparse_to_jinja2 import convert as _convert_atparse_to_jinja2
from uwtools.config.formats.yaml import YAMLConfig as _YAMLConfig
from uwtools.config.tools import compare_configs as _compare
from uwtools.config.tools import realize_config as _realize
from uwtools.config.validator import validate_yaml_config as _validate_yaml_config
from uwtools.config.validator import validate_yaml_file as _validate_yaml_file
from uwtools.types import DefinitePath, OptionalPath
from uwtools.utils.file import FORMAT as _FORMAT


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
    ???
    """
    return _realize(
        input_file=input_file,
        input_format=input_format,
        output_file=output_file,
        output_format=output_format,
        values_file=values_file,
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


def validate(schema_file: DefinitePath, config: Union[dict, _YAMLConfig, OptionalPath]) -> bool:
    """
    ???
    """
    if isinstance(config, dict):
        with NamedTemporaryFile(mode="w", encoding="utf-8") as f:
            yaml.dump({}, f)
        cfgobj = _YAMLConfig(f.name)
        cfgobj.data = config
        return _validate_yaml_config(schema_file=schema_file, config=cfgobj)
    if isinstance(config, _YAMLConfig):
        return _validate_yaml_config(schema_file=schema_file, config=config)
    return _validate_yaml_file(schema_file=schema_file, config_file=config)
