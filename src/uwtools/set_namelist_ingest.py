#!/usr/bin/env python3

'''
This utility demonstrates the ingest functions to update a Fortran namelist file
using the f90nml package while using a Jinja2 templated input file that is
filled in from the user environment
'''

import os
import sys
import argparse

from jinja2 import Environment, FileSystemLoader, meta
import f90nml

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
    parser.add_argument('-i', '--input_nml',
                       required=True,
                       help='Path to a templated user namelist.',
                       )
    # switch for printing to stdout the f90 namelist output file
    parser.add_argument('-d', '--dry_run',
                       action='store_true',
                       help='If provided, suppress all output.',
                       )
    # switch for printing to stdout the required values needed to filled in by the template
    parser.add_argument('-v', '--values_needed',
                       action='store_true',
                       help='If provided, suppress all output.',
                       )

    return parser.parse_args(argv)

def set_namelist_ingest(argv):
    '''Main section for set_namelist ingest utility'''

    cla = parse_args(argv)

    jinja_template_file = cla.input_nml
    f90nml_file = cla.outfile

    cla = parse_args(argv)

    # instantiate Jinja2 to environment and set template input files to the top of the filesystem
    env = Environment(loader=FileSystemLoader(searchpath='/'), trim_blocks=True, lstrip_blocks=True)
    # retrieve user jinja2 input file for specific model namelist
    template = env.get_template(jinja_template_file)
    # for simplicity we render the fields for namelist file from user environment variables
    f90nml_object = template.render(**os.environ)
    # instantiate Python lib's f90nml Parser Object
    parser = f90nml.Parser()
    # write out fully qualified and populated f90 namelist file
    nml = parser.reads(f90nml_object)


    if cla.dry_run or cla.values_needed:
        if cla.outfile:
            print(f'warning file {f90nml_file} not written when using --dry_run or --values_needed')
    # apply switch to allow user to view the results of namelist instead of writing to disk
    if cla.dry_run:
        print(nml)
    # apply switch to print out required template values
    if cla.values_needed:
        with open(jinja_template_file,encoding='utf-8') as file:
            j2_parsed = env.parse(file.read())
            for each_var in meta.find_undeclared_variables(j2_parsed):
                print(each_var)
    # write out f90 name list
    if not cla.dry_run and not cla.values_needed:
        with open(f90nml_file, 'w+', encoding='utf-8') as nml_file:
            f90nml.write(nml, nml_file)

if __name__ == '__main__':
    set_namelist_ingest(sys.argv[1:])
