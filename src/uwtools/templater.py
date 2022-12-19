#!/usr/bin/env python3

'''
This utility renders a Jinja2 template using user-supplied configuration options
via YAML or environment variables.
'''

import os
import sys
import argparse

from uwtools.j2template import J2Template
from uwtools import config
from uwtools.logger import Logger

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
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='If provided, print all logging messages.',
        )
    parser.add_argument(
        '-q', '--quiet',
        action='store_true',
        help='If provided, print no logging messages',
        )
    return parser.parse_args(argv)

def set_template(argv):
    '''Main section for rendering and writing a template file'''
    user_args = parse_args(argv)

    logfile = os.path.join(os.path.dirname(__file__), "templater.log")
    log = Logger(level='info',
        _format='%(message)s',
        colored_log= False,
        logfile_path=logfile
        )
    if user_args.verbose:
        log.handlers.clear()
        log = Logger(level='debug',
            _format='%(asctime)s - %(levelname)-8s - %(name)-12s: %(message)s',
            colored_log= True,
            logfile_path=logfile
            )
        log.debug(r"Finished setting up debug file logging in {logfile}".format(logfile=logfile))
    elif user_args.quiet:
        log.handlers.clear()
        log.propagate = False



    log.info(f"""Running script templater.py with args:
{('-' * 70)}
{('-' * 70)}""")
    for name, val in user_args.__dict__.items():
        if name not in ["config"]:
            log.info("{name:>15s}: {val}".format(name=name, val=val))
    log.info(f"""{('-' * 70)}
{('-' * 70)}""")


    if user_args.config_file:
        cfg = config.YAMLConfig(user_args.config_file)
    else:
        cfg = os.environ

    if user_args.config_items:
        user_settings = dict_from_config_args(user_args.config_items)
        cfg.update(user_settings)

    # instantiate Jinja2 environment and template
    template = J2Template(cfg, user_args.input_template)

    if user_args.values_needed:
        # Gather the undefined template variables
        undeclared_variables = template.undeclared_variables
        log.info('Values needed for this template are:')
        for var in sorted(undeclared_variables):
            log.info(var)
        return

    if user_args.dry_run:
        if user_args.outfile:
            log.info(r"warning file {outfile} not written when using --dry_run".format(outfile=user_args.outfile))
        # apply switch to allow user to view the results of rendered template
        # instead of writing to disk
        # Render the template with the specified config object
        rendered_template = template.render_template()
        log.info(rendered_template)
    else:
        # write out rendered template to file
        template.dump_file(user_args.outfile)

if __name__ == '__main__':
    set_template(sys.argv[1:])
