"""
Support for rendering a Jinja2 template using user-supplied configuration options via YAML or
environment variables.
"""
import os
from typing import List

from uwtools import config
from uwtools.j2template import J2Template
from uwtools.logger import Logger
from uwtools.utils import cli_helpers


def render(
    config_file: str,
    config_items: List[str],
    input_template: str,
    outfile: str,
    log: Logger,
    dry_run: bool = False,
    values_needed: bool = False,
) -> None:
    """
    Render a Jinja2 template using user-supplied configuration options via YAML or environment
    variables.
    """
    cfg = _set_up_config_obj(config_file=config_file, config_items=config_items, log=log)

    # Instantiate Jinja2 environment and template.
    template = J2Template(cfg, input_template, log_name=log.name)

    undeclared_variables = template.undeclared_variables

    if values_needed:
        # Gather the undefined template variables.
        log.info("Values needed for this template are:")
        for var in sorted(undeclared_variables):
            log.info(var)
        return

    # Check for missing values.
    missing = []
    for var in undeclared_variables:
        if var not in cfg.keys():
            missing.append(var)

    if missing:
        log.critical("ERROR: Template requires variables that are not provided")
        for key in missing:
            log.critical(f"  {key}")
        msg = "Missing values needed by template"
        log.critical(msg)
        raise ValueError(msg)

    if dry_run:
        # Apply switch to allow user to view the results of rendered template
        # instead of writing to disk. Render the template with the specified
        # config object.
        rendered_template = template.render_template()
        log.info(rendered_template)
    else:
        # Write out rendered template to file.
        template.dump_file(outfile)


def _set_up_config_obj(config_file: str, config_items: List[str], log: Logger) -> dict:
    """
    Return a dictionary config object from a user-supplied config, the shell environment, and the
    command line arguments.
    """
    if config_file:
        config_type = cli_helpers.get_file_type(config_file)
        cfg_obj = getattr(config, f"{config_type}Config")
        cfg = cfg_obj(config_file)
        log.debug("User config will be used to fill template.")
    else:
        cfg = dict(os.environ)  # Do not modify os.environ: Make a copy.
        log.debug("Environment variables will be used to fill template.")
    if config_items:
        user_settings = cli_helpers.dict_from_config_args(config_items)
        cfg.update(user_settings)
        log.debug("Overwriting config with settings on command line")
    return cfg
