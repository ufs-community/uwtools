"""
API access to ``uwtools`` templating logic.
"""

import os
from pathlib import Path
from typing import Optional, Union

from uwtools.config.atparse_to_jinja2 import convert as _convert_atparse_to_jinja2
from uwtools.config.jinja2 import render as _render
from uwtools.exceptions import UWTemplateRenderError
from uwtools.utils.api import ensure_data_source as _ensure_data_source
from uwtools.utils.api import str2path as _str2path


def render(
    values_src: Optional[Union[dict, Path, str]] = None,
    values_format: Optional[str] = None,
    input_file: Optional[Union[Path, str]] = None,
    output_file: Optional[Union[Path, str]] = None,
    overrides: Optional[dict[str, str]] = None,
    env: bool = False,
    searchpath: Optional[list[str]] = None,
    values_needed: bool = False,
    dry_run: bool = False,
    stdin_ok: bool = False,
) -> str:
    """
    Render a Jinja2 template to a file, based on specified values.

    Primary values used to render the template are taken from the specified file. The format of the
    values source will be deduced from the filename extension, if possible. This can be overridden
    via the ``values_format`` argument. A ``dict`` object may alternatively be provided as the
    primary values source. If no input file is specified, ``stdin`` is read. If no output file is
    specified, ``stdout`` is written to.

    :param values_src: Source of values to render the template
    :param values_format: Format of values when sourced from file
    :param input_file: Path to read raw Jinja2 template from (``None`` or unspecified => read
        ``stdin``)
    :param output_file: Path to write rendered Jinja2 template to (``None`` or unspecified => write
        to ``stdout``)
    :param overrides: Supplemental override values
    :param env: Supplement values with environment variables?
    :param searchpath: Paths to search for extra templates
    :param values_needed: Just report variables needed to render the template?
    :param dry_run: Run in dry-run mode?
    :param stdin_ok: OK to read from ``stdin``?
    :return: The rendered template string
    :raises: UWTemplateRenderError if template could not be rendered
    """
    result = _render(
        values_src=_str2path(values_src),
        values_format=values_format,
        input_file=_ensure_data_source(_str2path(input_file), stdin_ok),
        output_file=_str2path(output_file),
        overrides=overrides,
        env=env,
        searchpath=searchpath,
        values_needed=values_needed,
        dry_run=dry_run,
    )
    if result is None:
        raise UWTemplateRenderError("Could not render template")
    return result


def render_to_str(  # pylint: disable=unused-argument
    values_src: Optional[Union[dict, Path, str]] = None,
    values_format: Optional[str] = None,
    input_file: Optional[Union[Path, str]] = None,
    overrides: Optional[dict[str, str]] = None,
    env: bool = False,
    searchpath: Optional[list[str]] = None,
    values_needed: bool = False,
    dry_run: bool = False,
) -> str:
    """
    Render a Jinja2 template to a string, based on specified values.

    See ``render()`` for details on arguments, etc.
    """
    return render(**{**locals(), "output_file": Path(os.devnull)})


def translate(
    input_file: Optional[Union[Path, str]] = None,
    output_file: Optional[Union[Path, str]] = None,
    dry_run: bool = False,
    stdin_ok: bool = False,
) -> bool:
    """
    Translate an atparse template to a Jinja2 template.

    ``@[]`` tokens are replaced with Jinja2 ``{{}}`` equivalents. If no input file is specified,
    ``stdin`` is read. If no output file is specified, ``stdout`` is written to. In ``dry_run``
    mode, output is written to ``stderr``.

    :param input_file: Path to the template containing atparse syntax (``None`` or unspecified =>
        read ``stdin``)
    :param output_file: Path to the file to write the converted template to
    :param dry_run: Run in dry-run mode?
    :param stdin_ok: OK to read from ``stdin``?
    :return: ``True``
    """
    _convert_atparse_to_jinja2(
        input_file=_ensure_data_source(_str2path(input_file), stdin_ok),
        output_file=_str2path(output_file),
        dry_run=dry_run,
    )
    return True
