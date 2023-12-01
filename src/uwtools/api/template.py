from typing import Dict, Optional

from uwtools.config.jinja2 import render as _render
from uwtools.types import DefinitePath, OptionalPath


def render(
    values_file: DefinitePath,
    values_format: Optional[str] = None,
    input_file: OptionalPath = None,
    output_file: OptionalPath = None,
    overrides: Optional[Dict[str, str]] = None,
    values_needed: bool = False,
    dry_run: bool = False,
) -> bool:
    """
    ???
    """
    return _render(
        values_file=values_file,
        values_format=values_format,
        input_file=input_file,
        output_file=output_file,
        overrides=overrides,
        values_needed=values_needed,
        dry_run=dry_run,
    )
