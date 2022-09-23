#!/usr/bin/env python3
# pylint: disable=duplicate-code

'''
This utility updates a Fortran namelist file using the f90nml package. The
settings that are modified are supplied via command line YAML-formatted string
and/or YAML configuration files and a Name List Template in the form of a Jinja2 file.

The utility uses the key value pairs from the a given YAML configuration file which
in turn populates a Name List Jinja2 template and generates and Fortran Name List
file using python f90nml
'''

import sys
import os
import argparse

from uwtools.j2template import J2Template
from uwtools import config

def dict_from_config_args(args):
    '''Given a list of command line arguments in the form key=value, return a
    dictionary of key/value pairs.'''
    return dict([arg.split('=') for arg in args])

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
        'config_items',
        help='Any number of configuration settings that will override values '
        'found in YAML or user environment.',
        metavar='KEY=VALUE',
        nargs='*',
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

def set_namelist(argv):
    '''Main section for set_namelist utility'''

    user_args = parse_args(argv)

    if user_args.config_file:
        cfg = config.YAMLConfig(user_args.config_file)
    else:
        cfg = os.environ

    if user_args.config_items:
        user_settings = dict_from_config_args(user_args.config_items)
        cfg.update(user_settings)

    j2t_obj = J2Template(configure_obj=cfg, template_path=user_args.input_template)
    # NOTE: we added the option to get an F90Conifg object from a string as well as a file
    # with this option we do not have to write out a file from the above step
    nml = config.F90Config(string=j2t_obj.render_template())
    #nml = config.F90Config(config_path=path_to_file_if_used)

    if user_args.values_needed:
        j2t_obj.validate_config()

    if user_args.dry_run:
        # There are two output cases:
        # First the F90nml object itself
        print('nml.config_obj:\n',nml.config_obj)
        # and this one is same object after being recasted
        # via self.update to the inherited UserDict from the
        # abstract base class Config
        nl_name = list(nml)[0]
        print( nl_name )
        for key,value in nml[nl_name].items():
            print(f'  {key} = {value}'.format(key,value))
        if user_args.outfile is not None:
            print(f'to be written out to: {user_args.outfile}'.format(user_args.outfile))
        else:
            print('no file specified for outout')
    elif not user_args.dry_run and not user_args.values_needed:
        nml.dump_file(user_args.outfile)

if __name__ == '__main__':
    set_namelist(sys.argv[1:])
