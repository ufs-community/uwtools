"""
Support for rendering Jinja2 templates.
"""

import logging
import os
from typing import Dict, Optional

import uwtools.config.core
from uwtools.config.j2template import J2Template
from uwtools.types import DefinitePath, OptionalPath
from uwtools.utils.file import get_file_type, readable, writable


def render(
    input_file: OptionalPath,
    output_file: OptionalPath,
    config_file: DefinitePath,
    overrides: Optional[Dict[str, str]] = None,
    values_needed: bool = False,
    dry_run: bool = False,
) -> bool:
    """
    Render a Jinja2 template.

    :param input_file: Path to the Jinja2 template file to render.
    :param output_file: Path to the file to write the rendered Jinja2 template to.
    :param config_file: Path to the config file supplying values to render the template.
    :param keq_eq_val_pairs: "key=value" strings to supplement config-file values.
    :param values_needed: Just issue a report about variables needed to render the template?
    :param dry_run: Run in dry-run mode?
    """
    _report(locals())
    cfgobj = _set_up_config_obj(config_file=config_file, overrides=overrides)
    with readable(input_file) as f:
        template_str = f.read()
    template = J2Template(configure_obj=cfgobj, template_str=template_str)
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

    missing = [var for var in undeclared_variables if var not in cfgobj.keys()]
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
    dashes = lambda: logging.debug("-" * 69)
    logging.debug("Internal arguments:")
    dashes()
    for varname, value in args.items():
        logging.debug("%16s: %s", varname, value)
    dashes()


def _set_up_config_obj(
    config_file: OptionalPath = None, overrides: Optional[Dict[str, str]] = None
) -> dict:
    """
    Return a config object based on an input file, if given, or otherwise the shell environment; and
    supplemented with override values from given "key=value" strings.

    :param config_file: The config file to base the config object on.
    :param keq_eq_val_pairs: "key=value" strings to supplement config-file values.
    :returns: A config object.
    """
    if config_file:
        config_type = get_file_type(config_file)
        cfg_class = getattr(uwtools.config.core, f"{config_type}Config")
        cfg = cfg_class(config_file)
        logging.debug("Read initial config from %s", config_file)
    else:
        cfg = dict(os.environ)  # Do not modify os.environ: Make a copy.
        logging.debug("Initial config set from environment")
    if overrides:
        cfg.update(overrides)
        logging.debug("Update config with override values: %s", " ".join(overrides))
    return cfg
