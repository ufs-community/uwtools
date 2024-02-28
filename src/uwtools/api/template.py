"""
API access to uwtools templating logic.
"""
from pathlib import Path
from typing import Dict, Optional, Union

from uwtools.config.atparse_to_jinja2 import convert as _convert_atparse_to_jinja2
from uwtools.config.jinja2 import render as _render


def render(
    values: Union[dict, Path],
    values_format: Optional[str] = None,
    input_file: Optional[Path] = None,
    output_file: Optional[Path] = None,
    overrides: Optional[Dict[str, str]] = None,
    values_needed: bool = False,
    partial: bool = False,
    dry_run: bool = False,
) -> bool:
    """
    Render a Jinja2 template based on specified values.

    Primary values used to render the template are taken from the specified file. The format of the
    values source will be deduced from the filename extension, if possible. This can be overridden
    via the ``values_format`` argument. A ``dict`` object may alternatively be provided as the
    primary values source. If no input file is specified, ``stdin`` is read. If no output file is
    specified, ``stdout`` is written to.

    :param values: Source of values to render the template
    :param values_format: Format of values when sourced from file
    :param input_file: Path to read raw Jinja2 template from (``None`` or unspecified => read
        ``stdin``)
    :param output_file: Path to write rendered Jinja2 template to (``None`` or unspecified => write
        to ``stdout``)
    :param overrides: Supplemental override values
    :param values_needed: Just report variables needed to render the template?
    :param partial: Permit unrendered expressions in output?
    :param dry_run: Run in dry-run mode?
    :return: ``True`` if Jinja2 template was successfully rendered, ``False`` otherwise
    """
    return _render(
        values=values,
        values_format=values_format,
        input_file=input_file,
        output_file=output_file,
        overrides=overrides,
        values_needed=values_needed,
        partial=partial,
        dry_run=dry_run,
    )


def translate(
    input_file: Optional[Path] = None,
    output_file: Optional[Path] = None,
    dry_run: bool = False,
) -> bool:
    """
    Translate an atparse template to a Jinja2 template.

    ``@[]`` tokens are replaced with Jinja2 ``{{}}`` equivalents. If no input file is specified,
    ``stdin`` is read. If no output file is specified, ``stdout`` is written to. In ``dry_run``
    mode, output is written to ``stderr``.

    :param input_file: Path to the template containing atparse syntax
    :param output_file: Path to the file to write the converted template to
    :param dry_run: Run in dry-run mode?
    :return: ``True``
    """
    _convert_atparse_to_jinja2(input_file=input_file, output_file=output_file, dry_run=dry_run)
    return True
