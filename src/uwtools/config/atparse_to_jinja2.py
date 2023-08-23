"""
Utilities for rendering Jinja2 templates.
"""

import re
import sys
from typing import IO, Optional


def convert(input_template: str, outfile: Optional[str] = None, dry_run: bool = False) -> None:
    """
    Renders a Jinja2 template using user-supplied configuration options via YAML or environment
    variables.

    :param input_template: Path to the template containing atparse syntax.
    :param outfile: The file to write the converted template to.
    :param dry_run: Run in dry-run mode?
    :raises: RuntimeError if neither an output file or dry-run are specified.
    """

    def write(f_out: IO) -> None:
        with open(input_template, "r", encoding="utf-8") as f_in:
            for line in f_in:
                print(_replace(line.strip()), file=f_out)

    if dry_run:
        write(sys.stdout)
    elif outfile:
        with open(outfile, "w", encoding="utf-8") as out_f:
            write(out_f)
    else:
        raise RuntimeError("Provide an output path or specify dry-run mode.")


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
