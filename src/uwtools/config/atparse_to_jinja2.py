"""
Utilities for rendering Jinja2 templates.
"""

import re
import sys
from contextlib import contextmanager
from typing import IO, Generator, Optional, TextIO


@contextmanager
def readable(filename: Optional[str] = None) -> Generator[TextIO, None, None]:
    """
    ???
    """
    if filename:
        with open(filename, "r", encoding="utf-8") as f:
            yield f
    else:
        yield sys.stdin


def convert(
    input_file: Optional[str] = None, output_file: Optional[str] = None, dry_run: bool = False
) -> None:
    """
    Replaces atparse @[] tokens with Jinja2 {{}} equivalents.

    If no input file is given, stdin is used. If no output file is given, stdout is used. In dry-run
    mode, output is written to stderr.

    :param input_file: Path to the template containing atparse syntax.
    :param output_file: Path to the file to write the converted template to.
    :param dry_run: Run in dry-run mode?
    :raises: RuntimeError if neither an output file or dry-run are specified.
    """

    def write(f_out: IO) -> None:
        with readable(input_file) as f_in:
            for line in f_in:
                print(_replace(line.strip()), file=f_out)

    if dry_run:
        write(sys.stderr)
    elif output_file:
        with open(output_file, "w", encoding="utf-8") as out_f:
            write(out_f)
    else:
        write(sys.stdout)


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
