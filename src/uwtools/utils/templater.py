"""
Support for rendering a Jinja2 template.
"""
import os
from typing import List, Optional

from uwtools import config
from uwtools.j2template import J2Template
from uwtools.logger import Logger
from uwtools.utils import cli_helpers


def render(
    config_file: Optional[str],
    key_eq_val_pairs: List[str],
    input_template: str,
    outfile: str,
    log: Logger,
    dry_run: bool = False,
    values_needed: bool = False,
) -> None:
    """
    Render a Jinja2 template using values fro an input file.

    :param config_file: Path to the config file supplying values to render the template.
    :param keq_eq_val_pairs: "key=value" strings to supplement config-file values.
    :param input_template: Path to the Jinja2 template file to render.
    :param outfile: Path to the file to write the rendered Jinja2 template to.
    :param log: A logger.
    :param dry_run: Run in dry-run mode?
    :param values_needed: Just issue a report about variables needed to render the template? :raises
        ValueError if values needed to render the template are missing.
    """
    cfg = _set_up_config_obj(config_file=config_file, key_eq_val_pairs=key_eq_val_pairs, log=log)
    template = J2Template(cfg, input_template, log_name=log.name)
    undeclared_variables = template.undeclared_variables

    # If a report of variables required to render the template was requested, make that report and
    # then return.

    if values_needed:
        log.info("Values needed to render this template are:")
        for var in sorted(undeclared_variables):
            log.info(var)
        return

    # Check for missing values required to render the template. If found, report them and abort.

    missing = []
    for var in undeclared_variables:
        if var not in cfg.keys():
            missing.append(var)
    if missing:
        msg = "Template requires values that were not provided:"
        log.critical(msg)
        for key in missing:
            log.critical(key)
        raise ValueError(msg)

    # In dry-run mode, display the rendered template and then return.

    if dry_run:
        rendered_template = template.render_template()
        for line in rendered_template.split("\n"):
            log.info(line)
        return

    # Write rendered template to file.

    template.dump_file(outfile)


def _set_up_config_obj(
    config_file: Optional[str], key_eq_val_pairs: List[str], log: Logger
) -> dict:
    """
    Return a config object based on an input file, if given, or otherwise the shell environment; and
    supplemented with override values from given "key=value" strings.

    :param config_file: The config file to base the config object on.
    :param keq_eq_val_pairs: "key=value" strings to supplement config-file values.
    :param log: A logger.
    :returns: A config object.
    """
    if config_file:
        config_type = cli_helpers.get_file_type(config_file)
        cfg_class = getattr(config, f"{config_type}Config")
        cfg = cfg_class(config_file)
        log.debug("Read initial config from %s", config_file)
    else:
        cfg = dict(os.environ)  # Do not modify os.environ: Make a copy.
        log.debug("Initial config set from environment")
    if key_eq_val_pairs:
        supplemental = cli_helpers.dict_from_key_eq_val_strings(key_eq_val_pairs)
        cfg.update(supplemental)
        log.debug("Supplemented config with values: %s", " ".join(key_eq_val_pairs))
    return cfg
