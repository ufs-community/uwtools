# pylint: disable=unused-import

import uwtools.config.atparse_to_jinja2
import uwtools.config.validator
from uwtools.config.tools import compare_configs as compare
from uwtools.config.tools import realize_config as realize
from uwtools.utils.file import FORMAT, DefinitePath


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
    success = True
    if input_format == FORMAT.atparse and output_format == FORMAT.jinja2:
        uwtools.config.atparse_to_jinja2.convert(
            input_file=input_file,
            output_file=output_file,
            dry_run=dry_run,
        )
    else:
        success = False
    return success


def validate(input_file: DefinitePath, input_format: str, schema_file: DefinitePath) -> bool:
    """
    ???
    """
    success = True
    if input_format == FORMAT.yaml:
        success = uwtools.config.validator.validate_yaml(
            config_file=input_file, schema_file=schema_file
        )
    else:
        success = False
    return success
