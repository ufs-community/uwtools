"""
Utilities for rendering Jinja2 templates.
"""

import re
from typing import Optional


def convert(input_template: str, dry_run: bool = False, outfile: Optional[str] = None) -> None:
    """
    Renders a Jinja2 template using user-supplied configuration options via YAML or environment
    variables.
    """
    with open(input_template, "rt", encoding="utf-8") as atparsetemplate:
        if dry_run:
            for line in atparsetemplate:
                print(_replace(line))
        else:
            assert outfile is not None
            with open(outfile, "wt", encoding="utf-8") as jinja2template:
                for line in atparsetemplate:
                    jinja2template.write(_replace(line))


def _replace(atline: str) -> str:
    """
    Replace @[] with {{}} in a line of text.
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
