"""
This utility renders a Jinja2 template using user-supplied configuration options
via YAML or environment variables.
"""

import re
import sys
from argparse import ArgumentParser, HelpFormatter

from uwtools.utils import cli_helpers


def parse_args(args):
    """
    Function maintains the arguments accepted by this script. Please see
    Python's argparse documentation for more information about settings of each
    argument.
    """
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
    return parser.parse_args(args)


def atparse_replace(atline):
    """Function to replace @[] with {{}} in a line of text."""

    while re.search(r"\@\[.*?\]", atline):
        # Set maxsplits to 1 so only first @[ is captured
        before_atparse = atline.split("@[", 1)[0]
        within_atparse = atline.split("@[")[1].split("]")[0]

        # Set maxsplits to 1 so only first ] is captured, which
        # should be the bracket closing @[
        after_atparse = atline.split("@[", 1)[1].split("]", 1)[1]
        atline = "".join([before_atparse, "{{", within_atparse, "}}", after_atparse])
    return atline


def main():
    """Main section for converting the template file"""

    user_args = parse_args(sys.argv[1:])
    with open(user_args.input_template, "rt", encoding="utf-8") as atparsetemplate:
        if user_args.dry_run:
            if user_args.outfile:
                print(f"warning file {user_args.outfile} not written when using --dry_run")
            for line in atparsetemplate:
                print(atparse_replace(line))
        else:
            with open(user_args.outfile, "wt", encoding="utf-8") as jinja2template:
                for line in atparsetemplate:
                    jinja2template.write(atparse_replace(line))
