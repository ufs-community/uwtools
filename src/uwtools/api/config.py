# pylint: disable=unused-import

from uwtools.config.atparse_to_jinja2 import convert as _a2j
from uwtools.config.tools import compare_configs as compare
from uwtools.config.tools import realize_config as realize
from uwtools.config.validator import validate_yaml as _validate
from uwtools.types import DefinitePath
from uwtools.utils.file import FORMAT


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
