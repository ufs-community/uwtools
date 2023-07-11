# pylint: disable=duplicate-code
"""
CLI for rendering a Jinja2 template using user-supplied configuration options via YAML or
environment variables.
"""

import inspect
import sys
from argparse import ArgumentError, ArgumentParser, HelpFormatter, Namespace
from typing import List

from uwtools.utils import cli_helpers, templater


def main() -> None:
    """
    Main entry point.
    """
    args = parse_args(sys.argv[1:])
    name = f"{inspect.stack()[0][3]}"
    log = cli_helpers.setup_logging(
        log_file=args.log_file, log_name=name, quiet=args.quiet, verbose=args.verbose
    )
    dashes = lambda: log.info("{x}\n{x}".format(x=f"{('-' * 70)}"))
    log.info("Running with args:")
    dashes()
    for name, val in sorted(args.__dict__.items()):
        if name not in ["config"]:
            log.info("{name:>15s}: {val}".format(name=name, val=val))
    log.info("Re-run settings: %s", " ".join(sys.argv[1:]))
    dashes()
    templater.render(
        config_file=args.config_file,
        config_items=args.config_items,
        input_template=args.input_template,
        outfile=args.outfile,
        log=log,
        dry_run=args.dry_run,
        values_needed=args.values_needed,
    )


def parse_args(args: List[str]) -> Namespace:
    """
    Function maintains the arguments accepted by this script.

    Please see Python's argparse documentation for more information about settings of each argument.
    """
    args = args or ["--help"]
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
        default="/dev/null",
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
