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

import f90nml

from uwtools.jinja_config import Jinja2Config

class NlConfig(Jinja2Config):
    '''Name List Configure Class to support Name List Generation Utility Code'''
    def __init__(self, template_file=None, config_file=None):
        '''instantiate Jinja2 environment and set template input from files top of the filesystem'''
        super().__init__(template_file=template_file,config_file=config_file)
        self.nl_template = self.template

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

    # get values of command line arguments into cla
    cla = parse_args(argv)
    # instantiate a Name List Configuration Class which has already
    # inherited the YAMLFile Class and its methods such as include
    name_list = NlConfig(template_file=cla.template_input_nml)
    # using inherited include method from YAMLFile get YAML configure file
    yaml_config = name_list.yaml_include(config_file=cla.config)
    # get the Jinja2 template object from NlConfig attribute created by init
    template = name_list.nl_template
    # apply yaml_config and stringify Jinja2 template
    f90nml_object = template.render(yaml_config)
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
            for each_var in name_list.meta.find_undeclared_variables(j2_parsed):
                print(each_var)
    # write out f90 name list when not using query
    if not cla.dry_run and not cla.values_needed:
        with open(cla.outfile, 'w+', encoding='utf-8') as nml_file:
            f90nml.write(nml, nml_file)

if __name__ == '__main__':
    set_namelist_ingest(sys.argv[1:])
