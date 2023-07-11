# pylint: disable=duplicate-code
"""
CLI for rendering Jinja2 templates.
"""

import sys
from argparse import ArgumentParser, HelpFormatter, Namespace
from typing import List

from uwtools.utils import atparse_to_jinja2, cli_helpers


def main() -> None:
    """
    Main entry point.
    """
    args = parse_args(sys.argv[1:])
    atparse_to_jinja2.convert(
        input_template=args.input_template, outfile=args.outfile, dry_run=args.dry_run
    )


def parse_args(args: List[str]) -> Namespace:
    """
    Function maintains the arguments accepted by this script.

    Please see Python's argparse documentation for more information about settings of each argument.
    """
    args = args or ["--help"]
    parser = ArgumentParser(
        description="Convert an atparse template to Jinja2.",
        formatter_class=lambda prog: HelpFormatter(prog, max_help_position=8),
    )
    required = parser.add_argument_group("required arguments")
    required.add_argument(
        "-i",
        "--input-template",
        help="Path to an atparse template file",
        metavar="FILE",
        required=True,
        type=cli_helpers.path_if_file_exists,
    )
    optional = parser.add_argument_group("optional arguments")
    optional.add_argument(
        "-d",
        "--dry-run",
        action="store_true",
        help="Print rendered template to stdout only.",
    )
    optional.add_argument(
        "-o",
        "--outfile",
        help="Path to new Jinja2 template",
        metavar="FILE",
    )
    parsed = parser.parse_args(args)
    if not parsed.dry_run and not parsed.outfile:
        print("Specify either --dry-run or --outfile", file=sys.stderr)
        sys.exit(1)
    return parsed
