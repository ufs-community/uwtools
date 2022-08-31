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

from uwtools import config
from uwtools.J2Template import J2Template

def parse_args(argv):

    '''
    Function maintains the arguments accepted by this script. Please see
    Python's argparse documentation for more information about settings of each
    argument.
    '''

    parser = argparse.ArgumentParser(
       description='Update a Fortran namelist with user-defined settings.'
    )
    # output file (must be fully qualified path) true to
    # spec f90 name list file from python lib f90nml
    parser.add_argument('-o', '--outfile',
                       help='Full path to output file. This is a \
                       namelist by default.',
                       required=False,
                       )
    # Jinja2 user input file as a template to moc f90 name list file
    parser.add_argument('-i', '--template_input_nml',
                       required=True,
                       help='Path to a templated namelist.',
                       )
    # YAML config file for name list generation containing name list values
    parser.add_argument('-c', '--config',
                       required=False,
                       help='Path ito yaml configuration file for setting f90 name list generation',
                       )
    # single switch for printing to stdout the f90 namelist output file
    parser.add_argument('-d', '--dry_run',
                       action='store_true',
                       help='If provided, suppress writing out file and redirect to stdout.',
                       )

    # switch for printing to stdout the required values needed to filled in by the template
    parser.add_argument('--values_needed',
                       action='store_true',
                       help='If provided, suppress all output.',
                       )


    parser.add_argument("--set",
                        metavar="KEY=VALUE",
                        nargs='*',
                        help="Set a number of key-value pairs "
                             "(do not put spaces before or after the = sign). "
                        )

    return parser.parse_args(argv)

def get_nl_values(cla):
    '''get name list values to be filled designated by command line'''

    def file_exists_and_readable(check_file):
        if os.path.isfile(check_file):
            if not os.access(check_file, os.R_OK):
                print(f"File {check_file} exists but is is not readable")
                sys.exit(-1)
        else:
            print(f"File {check_file} does not exist")
            sys.exit(-1)

    file_exists_and_readable(cla.template_input_nml)
    if cla.config is not None:
        file_exists_and_readable(cla.config)

        nl_values_yaml = config.YAMLConfig(config_path=cla.config)
        nl_values_yaml.parse_include(config_file=cla.config,from_environment=True)
        if cla.set is not None:
            nl_commandline_values = dict(map(lambda s: s.split('='), cla.set))
            nl_values_yaml.parse_include(data=nl_commandline_values)

    if cla.config is None and cla.set is not None:
        nl_values_yaml = dict(map(lambda s: s.split('='), cla.set))

    if cla.config is None and cla.set is None:
        print("No values for templating name list were given. Defaultng to environment variables only") #pylint: disable=line-too-long
        nl_values_yaml = os.environ.copy()

    return nl_values_yaml


def set_namelist(argv):
    '''Main section for set_namelist utility'''

    cla = parse_args(argv)
    nl_values = get_nl_values(cla)

    j2t_obj = J2Template(data=nl_values,template_path=cla.template_input_nml)
    nml = config.F90Config(data=j2t_obj.render_template())

    if cla.values_needed:
        #for values in j2t_obj.undeclared_variables():
        #    print(values)
        j2t_obj.validate_config()
    if cla.dry_run:
        print(nml.config_obj)
        print(cla.outfile)
    elif not cla.dry_run and not cla.values_needed:
        print('writing to',cla.outfile)
        nml.dump_file(cla.outfile)

if __name__ == '__main__':
    set_namelist(sys.argv[1:])
