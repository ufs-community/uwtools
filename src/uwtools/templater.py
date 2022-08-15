#!/usr/bin/env python3

'''
This utility renders a Jinja2 template using user-supplied configuration options
via YAML or environment variables.
'''

import os
import sys
import argparse

from jinja2 import Environment, FileSystemLoader, meta
import f90nml

from uwtools import config

def file_exists(arg):
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
        type=file_exists,
        )
    parser.add_argument(
        '-c', '--config_file',
        help='Optional path to a YAML configuration file. If not provided, '
        'os.environ is used to configure.',
        type=file_exists,
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
    '''Main section for set_namelist ingest utility'''

    cla = parse_args(argv)

    if cla.config_file:
        cfg = config.YAMLConfig(cla.config_file)
    else:
        cfg = os.environ


    # instantiate Jinja2 environment and template
    env = Environment(loader=FileSystemLoader(cla.input_template))
    template = env.get_template('')

    # Gather the undefined template variables
    j2_parsed = env.parse(env.loader.get_source(env, ''))
    undeclared_variables = meta.find_undeclared_variables(j2_parsed)


    # Render the template with the specified config object
    rendered_template = template.render(**cfg)

    parser = f90nml.Parser()
    # write out fully qualified and populated f90 namelist file
    nml = parser.reads(rendered_template)

    if cla.dry_run or cla.values_needed:
        if cla.outfile:
            print(f'warning file {cla.outfile} not written when using --dry_run or --values_needed')
    # apply switch to allow user to view the results of namelist instead of writing to disk
    if cla.dry_run:
        print(nml)
    # apply switch to print out required template values
    if cla.values_needed:
        for var in undeclared_variables:
            print(var)
    # write out f90 name list
    if not cla.dry_run and not cla.values_needed:
        with open(cla.outfile, 'w+', encoding='utf-8') as nml_file:
            f90nml.write(nml, nml_file)

if __name__ == '__main__':
    set_template(sys.argv[1:])
