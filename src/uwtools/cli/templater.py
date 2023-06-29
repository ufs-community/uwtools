# pylint: disable=duplicate-code

"""
This utility renders a Jinja2 template using user-supplied configuration options
via YAML or environment variables.
"""

import inspect
import logging
import os
import sys
from argparse import ArgumentError, ArgumentParser, HelpFormatter

from uwtools import config
from uwtools.j2template import J2Template
from uwtools.utils import cli_helpers


def parse_args(args):
    """
    Function maintains the arguments accepted by this script. Please see
    Python's argparse documentation for more information about settings of each
    argument.
    """

    parser = ArgumentParser(
        description="Update a Jinja2 template with user-defined settings.",
        formatter_class=lambda prog: HelpFormatter(prog, max_help_position=8),
    )
    required = parser.add_argument_group("required arguments")
    required.add_argument(
        "-i",
        "--input-template",
        help="Path to a Jinja2 template file",
        required=True,
        type=cli_helpers.path_if_file_exists,
    )
    optional = parser.add_argument_group("optional arguments")
    optional.add_argument(
        "-c",
        "--config-file",
        help=(
            "Path to a YAML configuration file. "
            "If not provided, the environment is used to configure."
        ),
        metavar="FILE",
        type=cli_helpers.path_if_file_exists,
    )
    optional.add_argument(
        "-d",
        "--dry-run",
        action="store_true",
        help="Only print rendered template.",
    )
    optional.add_argument(
        "-l",
        "--log-file",
        # #PM# WHAT TO DO ABOUT THIS LOGDFILE PATH?
        default="/dev/null",  # os.path.join(os.path.dirname(__file__), "templater.log"),
        help="Path to a specified log file",
        metavar="FILE",
    )
    optional.add_argument(
        "-o",
        "--outfile",
        help="Path to output file",
        metavar="FILE",
    )
    optional.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        help="Print no log messages.",
    )
    optional.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Print more detailed log messages.",
    )
    optional.add_argument(
        "--values-needed",
        action="store_true",
        help="Print a list of required configuration settings.",
    )
    optional.add_argument(
        "config_items",
        help=(
            "Any number of configuration settings that will override values "
            "from config files or the environments"
        ),
        metavar="KEY=VALUE",
        nargs="*",
    )

    parsed = parser.parse_args(args)
    if not parsed.outfile and not parsed.dry_run and not parsed.values_needed:
        msg = "You need outfile, dry_run, or values_needed to continue."
        raise ArgumentError(None, msg)

    if parsed.quiet and parsed.dry_run:
        msg = "You added quiet and dry_run arguments. This will print nothing."
        raise ArgumentError(None, msg)

    return parsed


def setup_config_obj(user_args, log_name=None):
    """Return a dictionary config object from a user-supplied config,
    the os environment, and the command line arguments."""

    log = logging.getLogger(log_name)
    if user_args.config_file:
        config_type = cli_helpers.get_file_type(user_args.config_file)
        cfg_obj = getattr(config, f"{config_type}Config")
        cfg = cfg_obj(user_args.config_file)
        log.debug("User config will be used to fill template.")
    else:
        cfg = dict(os.environ)  # Do not modify os.environ: Make a copy.
        log.debug("Environment variables will be used to fill template.")

    if user_args.config_items:
        user_settings = cli_helpers.dict_from_config_args(user_args.config_items)
        cfg.update(user_settings)
        log.debug("Overwriting config with settings on command line")

    return cfg


def main():
    """Main section for rendering and writing a template file"""
    user_args = parse_args(sys.argv[1:])

    name = f"{inspect.stack()[0][3]}"
    log = cli_helpers.setup_logging(
        log_file=user_args.log_file, log_name=name, quiet=user_args.quiet, verbose=user_args.verbose
    )

    log.info("Running with args:")
    log.info(f"{('-' * 70)}")
    log.info(f"{('-' * 70)}")
    for name, val in user_args.__dict__.items():
        if name not in ["config"]:
            log.info("{name:>15s}: {val}".format(name=name, val=val))
    log.info(f"{('-' * 70)}")
    log.info(f"{('-' * 70)}")

    cfg = setup_config_obj(user_args, log_name=log.name)

    # instantiate Jinja2 environment and template
    template = J2Template(cfg, user_args.input_template, log_name=log.name)

    undeclared_variables = template.undeclared_variables

    if user_args.values_needed:
        # Gather the undefined template variables
        log.info("Values needed for this template are:")
        for var in sorted(undeclared_variables):
            log.info(var)
        return

    # Check for missing values
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

    if user_args.dry_run:
        if user_args.outfile:
            log.info(
                r"warning file {outfile} ".format(outfile=user_args.outfile),
                r"not written when using --dry_run",
            )
        # apply switch to allow user to view the results of rendered template
        # instead of writing to disk
        # Render the template with the specified config object
        rendered_template = template.render_template()
        log.info(rendered_template)
    else:
        # write out rendered template to file
        template.dump_file(user_args.outfile)
