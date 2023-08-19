"""
Utilities for rendering Jinja2 templates.
"""

import re
from typing import Optional


def convert(input_template: str, outfile: Optional[str] = None, dry_run: bool = False) -> None:
    """
    Renders a Jinja2 template using user-supplied configuration options via YAML or environment
    variables.

    :param input_template: Path to the template containing atparse syntax.
    :param outfile: The file to write the converted template to.
    :param dry_run: Run in dry-run mode?
    :raises: RuntimeError if neither an output file or dry-run are specified.
    """
    with open(input_template, "r", encoding="utf-8") as atparsetemplate:
        if dry_run:
            for line in atparsetemplate:
                print(_replace(line.strip()))
        elif outfile:
            with open(outfile, "w", encoding="utf-8") as jinja2template:
                for line in atparsetemplate:
                    jinja2template.write(_replace(line))
        else:
            raise RuntimeError("Provide an output path or run in dry-run mode.")


def _replace(atline: str) -> str:
    """
    Replace @[] with {{}} in a line of text.

    :param atline: A line (potentially) containing atparse syntax.
    :return: The given line with atparse syntax converted to Jinja2 syntax.
    """
    while re.search(r"\@\[.*?\]", atline):
        # Set maxsplits to 1 so only first @[ is captured.
        before_atparse = atline.split("@[", 1)[0]
        within_atparse = atline.split("@[")[1].split("]")[0]
        # Set maxsplits to 1 so only first ] is captured, which should be the
        # bracket closing @[.
        after_atparse = atline.split("@[", 1)[1].split("]", 1)[1]
        atline = "".join([before_atparse, "{{", within_atparse, "}}", after_atparse])
    return atline
