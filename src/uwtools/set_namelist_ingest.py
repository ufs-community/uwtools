#!/usr/bin/env python3

'''
This utility demonstrates the ingest functions to update a Fortran namelist file
using the f90nml package while using a Jinja2 templated input file that is
filled in from the user environment
'''

import argparse

import f90nml
import yaml
import jinja2
import os
import sys

from jinja2 import Environment, FileSystemLoader

def parse_args(argv):

     '''
     Function maintains the arguments accepted by this script. Please see
     Python's argparse documentation for more information about settings of each
     argument.
     '''

     parser = argparse.ArgumentParser(
        description='Update a Fortran namelist with user-defined settings.'
     )

     parser.add_argument('-o', '--outfile',
                        help='Full path to output file. This is a \
                        namelist by default.',
                        required=True,
                        )

     parser.add_argument('-i', '--input_nml',
                        help='Path to a templated user namelist.',
                        )

     parser.add_argument('-d', '--dry_run',
                        action='store_true',
                        help='If provided, suppress all output.',
                        )

     return parser.parse_args(argv)

def set_namelist_ingest(argv):

     cla = parse_args(argv)

     jinja_template_file = cla.input_nml
     f90nml_file = cla.outfile

     cla = parse_args(argv)

     env = Environment(loader = FileSystemLoader(searchpath='/'), trim_blocks=True, lstrip_blocks=True)
     template = env.get_template(jinja_template_file)
     f90nml_object = template.render(**os.environ)
     parser = f90nml.Parser()
     nml = parser.reads(f90nml_object)

     if cla.dry_run:
          print(nml)
     else:
          with open(f90nml_file, 'w+', encoding='utf-8') as nml_file:
              f90nml.write(nml, nml_file)

if __name__ == '__main__':
    set_namelist_ingest(sys.argv[1:])