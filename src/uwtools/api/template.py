"""
API access to ``uwtools`` templating logic.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING

from uwtools.config.atparse_to_jinja2 import convert as _convert_atparse_to_jinja2
from uwtools.config.jinja2 import render as _render
from uwtools.exceptions import UWTemplateRenderError
from uwtools.utils.api import ensure_data_source as _ensure_data_source
from uwtools.utils.file import str2path as _str2path

if TYPE_CHECKING:
    from datetime import datetime, timedelta


def render(
    values_src: dict | Path | str | None = None,
    values_format: str | None = None,
    input_file: Path | str | None = None,
    output_file: Path | str | None = None,
    cycle: datetime | None = None,
    leadtime: timedelta | None = None,
    overrides: dict[str, str] | None = None,
    env: bool = False,
    searchpath: list[str] | None = None,
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

    :param values_src: Source of values to render the template.
    :param values_format: Format of values when sourced from file.
    :param input_file: Raw input template file (``None`` => read ``stdin``).
    :param output_file: Rendered template output file (``None`` => write to ``stdout``).
    :param cycle: A datetime object to make available for use in templates.
    :param leadtime: A timedelta object to make available for use in templates.
    :param overrides: Supplemental override values.
    :param env: Supplement values with environment variables?
    :param searchpath: Paths to search for extra templates.
    :param values_needed: Just report variables needed to render the template?
    :param dry_run: Run in dry-run mode?
    :param stdin_ok: OK to read from ``stdin``?
    :return: The rendered template string.
    :raises: UWTemplateRenderError if template could not be rendered.
    """
    result = _render(
        values_src=_str2path(values_src),
        values_format=values_format,
        input_file=_ensure_data_source(_str2path(input_file), stdin_ok),
        output_file=_str2path(output_file),
        cycle=cycle,
        leadtime=leadtime,
        overrides=overrides,
        env=env,
        searchpath=searchpath,
        values_needed=values_needed,
        dry_run=dry_run,
    )
    if result is None:
        msg = "Could not render template"
        raise UWTemplateRenderError(msg)
    return result


def render_to_str(
    values_src: dict | Path | str | None = None,
    values_format: str | None = None,
    input_file: Path | str | None = None,
    overrides: dict[str, str] | None = None,
    env: bool = False,
    searchpath: list[str] | None = None,
    values_needed: bool = False,
    dry_run: bool = False,
) -> str:
    """
    Render a Jinja2 template to a string, based on specified values.

    See ``render()`` for details on arguments, etc.
    """
    return render(**{**locals(), "output_file": Path(os.devnull)})


def translate(
    input_file: Path | str | None = None,
    output_file: Path | str | None = None,
    dry_run: bool = False,
    stdin_ok: bool = False,
) -> bool:
    """
    Translate an atparse template to a Jinja2 template.

    ``@[]`` tokens are replaced with Jinja2 ``{{}}`` equivalents. If no input file is specified,
    ``stdin`` is read. If no output file is specified, ``stdout`` is written to. In ``dry_run``
    mode, output is written to ``stderr``.

    :param input_file: Path to atparse file (``None`` => read ``stdin``).
    :param output_file: Path to the file to write the converted template to.
    :param dry_run: Run in dry-run mode?
    :param stdin_ok: OK to read from ``stdin``?
    :return: ``True``.
    """
    _convert_atparse_to_jinja2(
        input_file=_ensure_data_source(_str2path(input_file), stdin_ok),
        output_file=_str2path(output_file),
        dry_run=dry_run,
    )
    return True
