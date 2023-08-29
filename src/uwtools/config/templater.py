"""
Support for rendering Jinja2 templates.
"""

import logging
import os
from typing import Dict, Optional

from uwtools.config.core import format_to_config
from uwtools.config.j2template import J2Template
from uwtools.logging import MSGWIDTH
from uwtools.types import DefinitePath, OptionalPath
from uwtools.utils.file import get_file_type, readable, writable


def render(
    input_file: OptionalPath,
    output_file: OptionalPath,
    values_file: DefinitePath,
    overrides: Optional[Dict[str, str]] = None,
    values_needed: bool = False,
    dry_run: bool = False,
) -> bool:
    """
    Render a Jinja2 template.

    :param input_file: Path to the Jinja2 template file to render.
    :param output_file: Path to the file to write the rendered Jinja2 template to.
    :param values_file: Path to the file supplying values to render the template.
    :param keq_eq_val_pairs: "key=value" strings to supplement values-file values.
    :param values_needed: Just issue a report about variables needed to render the template?
    :param dry_run: Run in dry-run mode?
    """
    _report(locals())
    values = _set_up_values_obj(values_file=values_file, overrides=overrides)
    with readable(input_file) as f:
        template_str = f.read()
    template = J2Template(values=values, template_str=template_str)
    undeclared_variables = template.undeclared_variables

    # If a report of variables required to render the template was requested, make that report and
    # then return.

    if values_needed:
        logging.info("Value(s) needed to render this template are:")
        for var in sorted(undeclared_variables):
            logging.info(var)
        return True

    # Check for missing values required to render the template. If found, report them and raise an
    # exception.

    missing = [var for var in undeclared_variables if var not in values.keys()]
    if missing:
        msg = "Required value(s) not provided:"
        logging.error(msg)
        for key in missing:
            logging.error(key)
        return False

    # In dry-run mode, display the rendered template and then return.

    if dry_run:
        rendered_template = template.render()
        for line in rendered_template.split("\n"):
            logging.info(line)
        return True

    # Write rendered template to file.

    with writable(output_file) as f:
        print(template.render(), file=f)
    return True


def _report(args: dict) -> None:
    """
    Log the names and values of arguments.

    :param args: The argument names and their values.
    """
    dashes = lambda: logging.debug("-" * MSGWIDTH)
    logging.debug("Internal arguments:")
    dashes()
    for varname, value in args.items():
        logging.debug("%16s: %s", varname, value)
    dashes()


def _set_up_values_obj(
    values_file: OptionalPath = None, overrides: Optional[Dict[str, str]] = None
) -> dict:
    """
    Collect template-rendering values based on an input file, if given, or otherwise on the shell
    environment; and supplemented with override values from given "key=value" strings.

    :param values_file: Path to the file supplying values to render the template.
    :param keq_eq_val_pairs: "key=value" strings to supplement values-file values.
    :returns: The collected values.
    """
    if values_file:
        values_type = get_file_type(values_file)
        values_class = format_to_config(values_type)
        values = values_class(values_file).data
        logging.debug("Read initial values from %s", values_file)
    else:
        values = dict(os.environ)  # Do not modify os.environ: Make a copy.
        logging.debug("Initial values taken from environment")
    if overrides:
        values.update(overrides)
        logging.debug("Updated values with overrides: %s", " ".join(overrides))
    return values
