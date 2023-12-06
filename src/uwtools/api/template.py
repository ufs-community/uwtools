from typing import Dict, Optional, Union

from uwtools.config.jinja2 import render as _render
from uwtools.types import DefinitePath, OptionalPath


def render(
    values: Union[dict, DefinitePath],
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
        values=values,
        values_format=values_format,
        input_file=input_file,
        output_file=output_file,
        overrides=overrides,
        values_needed=values_needed,
        dry_run=dry_run,
    )
