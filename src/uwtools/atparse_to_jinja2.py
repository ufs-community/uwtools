#!/usr/bin/env python3

'''
This utility renders a Jinja2 template using user-supplied configuration options
via YAML or environment variables.
'''
import re
import sys
import argparse

from uwtools.utils import cli_helpers

def parse_args(argv):

    '''
    Function maintains the arguments accepted by this script. Please see
    Python's argparse documentation for more information about settings of each
    argument.
    '''

    parser = argparse.ArgumentParser(
       description='Convert an atparse template to jinja2'
    )
    parser.add_argument(
        '-o', '--outfile',
        help='Full path to new jinja2 template',
        )
    parser.add_argument(
        '-i', '--input_template',
        help='Path to an atparse template file.',
        required=True,
        type=cli_helpers.path_if_file_exists,
        )

    parser.add_argument(
        '-d', '--dry_run',
        action='store_true',
        help='If provided, print rendered template to stdout only',
        )
    return parser.parse_args(argv)

def atparse_replace(atline):
    ''' Function to replace @[] with {{}} in a line of text. '''

    while re.search(r'\@\[.*?\]',atline):

#Set maxsplits to 1 so only first @[ is captured
        before_atparse = atline.split("@[",1)[0]
        within_atparse = atline.split("@[")[1].split("]")[0]

#Set maxsplits to 1 so only first ] is captured, which
#should be the bracket closing @[
        after_atparse = atline.split("@[",1)[1].split("]",1)[1]
        atline = ''.join([before_atparse,"{{",within_atparse,"}}", after_atparse])
    return atline

def convert_template(argv):
    ''' Main section for converting the template file'''

    user_args = parse_args(argv)
    with open(user_args.input_template, "rt", encoding="utf-8") as atparsetemplate:

        if user_args.dry_run:
            if user_args.outfile:
                print(f'warning file {user_args.outfile} not written when using --dry_run')
            for line in atparsetemplate:
                print(atparse_replace(line))
        else:
            with open(user_args.outfile, "wt", encoding="utf-8") as jinja2template:
                for line in atparsetemplate:
                    jinja2template.write(atparse_replace(line))

if __name__ == '__main__':
    convert_template(sys.argv[1:])
