"""
Convert atparse templates to Jinja2 templates.
"""

import re

from uwtools.logging import log
from uwtools.utils.file import OptionalPath, readable, writable


def convert(
    input_file: OptionalPath = None, output_file: OptionalPath = None, dry_run: bool = False
) -> None:
    """
    Replaces atparse @[] tokens with Jinja2 {{}} equivalents.

    If no input file is given, stdin is used. If no output file is given, stdout is used. In dry-run
    mode, output is written to stderr.

    :param input_file: Path to the template containing atparse syntax.
    :param output_file: Path to the file to write the converted template to.
    :param dry_run: Run in dry-run mode?
    """

    with readable(input_file) as f:
        lines = f.read().split("\n")
    jinja2 = "\n".join(_replace(line) for line in lines).rstrip()
    if dry_run:
        for line in jinja2.split("\n"):
            log.info(line)
    else:
        with writable(output_file) as f:
            print(jinja2, file=f)


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
        atline = "".join([before_atparse, "{{ ", within_atparse, " }}", after_atparse])
    return atline
