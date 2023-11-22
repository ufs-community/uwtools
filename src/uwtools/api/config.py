# pylint: disable=unused-import

from typing import Optional

from uwtools.config.atparse_to_jinja2 import convert as _a2j
from uwtools.config.tools import compare_configs as _compare
from uwtools.config.tools import realize_config as _realize
from uwtools.config.validator import validate_yaml as _validate
from uwtools.types import DefinitePath, OptionalPath
from uwtools.utils.file import FORMAT


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
    if input_format == FORMAT.atparse and output_format == FORMAT.jinja2:
        _a2j(input_file=input_file, output_file=output_file, dry_run=dry_run)
        return True
    return False


def validate(input_file: DefinitePath, input_format: str, schema_file: DefinitePath) -> bool:
    """
    ???
    """
    if input_format == FORMAT.yaml:
        return _validate(config_file=input_file, schema_file=schema_file)
    return False
