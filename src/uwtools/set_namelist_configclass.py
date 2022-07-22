#!/usr/bin/env python3
#pylint: disable=duplicate-code

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
import collections
import pathlib

import yaml
import f90nml
from jinja2 import Environment, FileSystemLoader, meta

from uwtools.loaders import load_yaml

class NlConfig():
    '''Name List Configure Class to support Name List Generation Utility Code'''
    def __init__(self, template_file=None, config_file=None):
        '''instantiate Jinja2 environment and set template input from files top of the filesystem'''
        self.j2env=Environment(loader=FileSystemLoader(searchpath='/'),
                               trim_blocks=True,lstrip_blocks=True)
        if config_file is not None:
            self.yaml_config = load_yaml(config_file)
        else:
            self.yaml_config = collections.UserDict()
        if template_file is not None:
            self.template_file = template_file
            self.nl_template = self.load_nl_j2_template(template_file)
        else:
            self.nl_template = None

    def load_yaml(self, config_file: pathlib.Path):
        '''Load dict safely using YAML. Return the resulting dict as UserDict Config object.'''
        with open(config_file,'r', encoding='utf-8') as _file:
            self.yaml_config = yaml.load(_file, Loader=yaml.SafeLoader)
        return self.yaml_config

    def load_nl_j2_template(self, _file: pathlib.Path):
        '''load jinja2 template file for a nl specific name list'''
        self.nl_template= self.j2env.get_template(_file)
        return self.nl_template


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

def set_namelist_ingest(argv):
    '''Main section for set_namelist ingest utility'''

    cla = parse_args(argv)

    name_list = NlConfig(cla.template_input_nml, cla.config)
    template = name_list.nl_template
    f90nml_object = template.render(name_list.yaml_config)
    # instantiate Python lib's f90nml Parser Object
    parser = f90nml.Parser()
    # write out fully qualified and populated f90 namelist file
    nml = parser.reads(f90nml_object)


    if cla.dry_run or cla.values_needed:
        if cla.outfile:
            print(f'warning file {cla.outfile} not written when using --dry_run or --values_needed')
    # apply switch to allow user to view the results of namelist instead of writing to disk
    if cla.dry_run:
        print(nml)
    # apply switch to print out required template values
    if cla.values_needed:
        with open(name_list.template_file ,encoding='utf-8') as file:
            j2_parsed = name_list.j2env.parse(file.read())
            for each_var in meta.find_undeclared_variables(j2_parsed):
                print(each_var)
    # write out f90 name list when not using query
    if not cla.dry_run and not cla.values_needed:
        with open(cla.outfile, 'w+', encoding='utf-8') as nml_file:
            f90nml.write(nml, nml_file)


if __name__ == '__main__':
    set_namelist_ingest(sys.argv[1:])
