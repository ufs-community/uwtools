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
import argparse

from uwtools.J2Template import J2Template
from uwtools.F90Config import F90Config

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
                       required=True,
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

    return parser.parse_args(argv)

def set_namelist(argv):
    '''Main section for set_namelist utility'''

    cla = parse_args(argv)
    j2t_obj = J2Template(configure_path=cla.config,template_path=cla.template_input_nml)
    nml = F90Config(data=j2t_obj.render_template())

    if cla.values_needed:
        for values in j2t_obj.undeclared_variables():
            print(values)
    if cla.dry_run:
        print(nml.config_obj)
    elif not cla.dry_run and not cla.values_needed:
        print('writing to',cla.outfile)
        nml.dump_file(cla.outfile)

if __name__ == '__main__':
    set_namelist(sys.argv[1:])
