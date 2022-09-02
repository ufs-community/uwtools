#!/usr/bin/env python3

'''
This utility renders a Jinja2 template using user-supplied configuration options
via YAML or environment variables.
'''

import os
import sys
import argparse

from jinja2 import Environment, FileSystemLoader, meta

from uwtools import config

def path_if_file_exists(arg):
    ''' Checks whether a file exists, and returns the path if it does. '''
    if not os.path.exists(arg):
        msg = f'{arg} does not exist!'
        raise argparse.ArgumentTypeError(msg)
    return arg

def parse_args(argv):

    '''
    Function maintains the arguments accepted by this script. Please see
    Python's argparse documentation for more information about settings of each
    argument.
    '''

    parser = argparse.ArgumentParser(
       description='Update a Jinja2 Template with user-defined settings.'
    )
    parser.add_argument(
        '-o', '--outfile',
        help='Full path to output file',
        )
    parser.add_argument(
        '-i', '--input_template',
        help='Path to a Jinja2 template file.',
        required=True,
        type=path_if_file_exists,
        )
    parser.add_argument(
        '-c', '--config_file',
        help='Optional path to a YAML configuration file. If not provided, '
        'os.environ is used to configure.',
        type=path_if_file_exists,
        )
    parser.add_argument(
        '-d', '--dry_run',
        action='store_true',
        help='If provided, print rendered template to stdout only',
        )
    parser.add_argument(
        '--values_needed',
        action='store_true',
        help='If provided, print a list of required configuration settings to stdout',
        )
    return parser.parse_args(argv)

def set_template(argv):
    '''Main section for rendering and writing a template file'''

    user_args = parse_args(argv)

    if user_args.config_file:
        cfg = config.YAMLConfig(user_args.config_file)
    else:
        cfg = os.environ


    # instantiate Jinja2 environment and template
    env = Environment(loader=FileSystemLoader(user_args.input_template))
    template = env.get_template('')

    # Gather the undefined template variables
    j2_parsed = env.parse(env.loader.get_source(env, ''))
    undeclared_variables = meta.find_undeclared_variables(j2_parsed)

    if user_args.values_needed:
        print('Values needed for this template are:')
        for var in sorted(undeclared_variables):
            print(var)

        return

    # Render the template with the specified config object
    rendered_template = template.render(**cfg)

    if user_args.dry_run:
        if user_args.outfile:
            print(f'warning file {user_args.outfile} not written when using --dry_run')
        # apply switch to allow user to view the results of rendered template instead of writing to disk
        print(rendered_template)
    else:
        # write out rendered template to file
        with open(user_args.outfile, 'w+', encoding='utf-8') as out_file:
            out_file.write(f'{rendered_template}')

if __name__ == '__main__':
    set_template(sys.argv[1:])
