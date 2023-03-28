#pylint: disable=unused-variable
"""
Tests for templater tool.
"""
from contextlib import redirect_stdout
import argparse
import io
import os
import tempfile
import logging

import pytest

from uwtools import templater

uwtools_file_base = os.path.join(os.path.dirname(__file__))

def compare_files(expected, actual):
    '''Compares the content of two files. Doing this over filecmp.cmp since we
    may not be able to handle end-of-file character differences with it.
    Prints the contents of two compared files to std out if they do not match.'''
    with open(expected, 'r', encoding='utf-8') as expected_file:
        expected_content = expected_file.read().rstrip('\n')
    with open(actual, 'r', encoding='utf-8') as actual_file:
        actual_content = actual_file.read().rstrip('\n')

    if expected_content != actual_content:
        print('The expected file looks like:')
        print(expected_content)
        print('*' * 80)
        print('The rendered file looks like:')
        print(actual_content)
        return False

    return True

def test_path_if_file_exists():
    """ Make sure the function works as expected. It is used as a type in
    argparse, so raises an argparse exception when the user provides a
    non-existent path"""

    with tempfile.NamedTemporaryFile(dir='.', mode='w') as tmp_file:
        assert templater.path_if_file_exists(tmp_file.name)

    with pytest.raises(argparse.ArgumentTypeError):
        not_a_filepath = './no_way_this_file_exists.nope'
        templater.path_if_file_exists(not_a_filepath)

def test_set_template_dryrun():
    """Unit test for checking dry-run output of ingest namelist tool"""

    input_file = os.path.join(uwtools_file_base, "fixtures/nml.IN")
    outcome=\
    """Running script templater.py with args:
----------------------------------------------------------------------
----------------------------------------------------------------------
        outfile: None
 input_template: """ + input_file  + """
    config_file: None
   config_items: []
        dry_run: True
  values_needed: False
        verbose: False
          quiet: False
----------------------------------------------------------------------
----------------------------------------------------------------------
&salad
  base = 'kale'
  fruit = 'banana'
  vegetable = 'tomato'
  how_many = 22
  dressing = 'balsamic'
/
"""
    os.environ['fruit'] = 'banana'
    os.environ['vegetable'] = 'tomato'
    os.environ['how_many'] = '22'

    args = [
         '-i', input_file,
         '--dry_run',
         ]

    # Capture stdout for the dry run
    outstring = io.StringIO()
    with redirect_stdout(outstring):
        templater.set_template(args)
    result = outstring.getvalue()

    assert result == outcome

def test_set_template_listvalues():
    """Unit test for checking values_needed output of ingest namelist tool"""

    input_file = os.path.join(uwtools_file_base, "fixtures/nml.IN")

    outcome=\
    """Running script templater.py with args:
----------------------------------------------------------------------
----------------------------------------------------------------------
        outfile: None
 input_template: """ + input_file  + """
    config_file: None
   config_items: []
        dry_run: False
  values_needed: True
        verbose: False
          quiet: False
----------------------------------------------------------------------
----------------------------------------------------------------------
Values needed for this template are:
fruit
how_many
vegetable
"""

    args = [
         '-i', input_file,
         '--values_needed',
         ]

    # Capture stdout for values_needed output
    outstring = io.StringIO()
    with redirect_stdout(outstring):
        templater.set_template(args)
    result = outstring.getvalue()

    assert result == outcome

def test_set_template_yaml_config():
    ''' Test that providing a YAML file with necessary settings works to fill in
    the Jinja template. Test the writing mechanism, too '''

    input_file = os.path.join(uwtools_file_base, "fixtures/nml.IN")
    config_file = os.path.join(uwtools_file_base, "fixtures/fruit_config.yaml")
    expected_file = os.path.join(uwtools_file_base, "fixtures/simple2.nml")

    # Also make sure that we're really pulling from the input file. Set
    # environment variables different from those in config_file
    os.environ['fruit'] = 'candy'
    os.environ['vegetable'] = 'cookies'
    os.environ['how_many'] = 'all'


    # Make sure the output file matches the expected output
    with tempfile.TemporaryDirectory(dir='.') as tmp_dir:
        out_file = f'{tmp_dir}/test_render_from_yaml.nml'

        args = [
             '-i', input_file,
             '-c', config_file,
             '-o', out_file,
             ]

        templater.set_template(args)
        assert compare_files(expected_file, out_file)

def test_set_template_command_line_config():
    '''Test that values provided on the command line produce the appropriate
    output.'''

    input_file = os.path.join(uwtools_file_base, "fixtures/nml.IN")

    outcome=\
    """Running script templater.py with args:
----------------------------------------------------------------------
----------------------------------------------------------------------
        outfile: None
 input_template: """ + input_file  + """
    config_file: None
   config_items: ['fruit=pear', 'vegetable=squash', 'how_many=22']
        dry_run: True
  values_needed: False
        verbose: False
          quiet: False
----------------------------------------------------------------------
----------------------------------------------------------------------
&salad
  base = 'kale'
  fruit = 'pear'
  vegetable = 'squash'
  how_many = 22
  dressing = 'balsamic'
/
"""

    args = [
         '-i', input_file,
         '--dry_run',
         'fruit=pear',
         'vegetable=squash',
         'how_many=22',
         ]

    # Capture stdout for the dry run
    outstring = io.StringIO()
    with redirect_stdout(outstring):
        templater.set_template(args)
    result = outstring.getvalue()
    assert result == outcome

def test_set_template_yaml_config_model_configure():
    '''Tests that the templater will work as expected for a simple model_configure
    file. '''

    input_file = os.path.join(uwtools_file_base,
                              "fixtures/model_configure.sample.IN")
    config_file = os.path.join(uwtools_file_base,
                               "fixtures/model_configure.values.yaml")
    expected_file = os.path.join(uwtools_file_base,
                                 "fixtures/model_configure.sample")

    # Make sure the output file matches the expected output
    with tempfile.TemporaryDirectory(dir='.') as tmp_dir:
        out_file = f'{tmp_dir}/test_render_from_yaml.nml'

        args = [
             '-i', input_file,
             '-c', config_file,
             '-o', out_file,
             ]

        templater.set_template(args)
        assert compare_files(expected_file, out_file)

def test_set_template_verbosity():
    """Unit test for checking dry-run output of ingest namelist tool"""

    input_file = os.path.join(uwtools_file_base, "fixtures/nml.IN")
    logfile = os.path.join(os.path.dirname(templater.__file__), "templater.log")
    trim_result = ''

    outcome=\
    """Finished setting up debug file logging in """ + logfile  + """
Running script templater.py with args:
----------------------------------------------------------------------
----------------------------------------------------------------------
        outfile: None
 input_template: """ + input_file  + """
    config_file: None
   config_items: []
        dry_run: True
  values_needed: False
        verbose: True
          quiet: False
----------------------------------------------------------------------
----------------------------------------------------------------------
&salad
  base = 'kale'
  fruit = 'banana'
  vegetable = 'tomato'
  how_many = 22
  dressing = 'balsamic'
/
"""

    os.environ['fruit'] = 'banana'
    os.environ['vegetable'] = 'tomato'
    os.environ['how_many'] = '22'

    #test verbose level
    args = [
         '-i', input_file,
         '--dry_run',
         '-v'
         ]

    # Capture verbose stdout
    outstring = io.StringIO()
    with redirect_stdout(outstring):
        templater.set_template(args)
    result = outstring.getvalue()

    lines = zip(outcome.split('\n'), result.split('\n'))
    for outcome_line, result_line in lines:
        # Check that only the correct messages were logged
        assert outcome_line in result_line

    #test quiet level
    args = [
         '-i', input_file,
         '--dry_run',
         '-q'
         ]

    # Capture quiet stdout
    outstring = io.StringIO()
    with redirect_stdout(outstring):
        templater.set_template(args)
    result = outstring.getvalue()

    outcome = ''
    # Check that only the correct messages were logged
    assert result == outcome

def test_log_passing():
    """Unit test for checking application of the logger object passing"""

    input_file = os.path.join(uwtools_file_base, "fixtures/nml.IN")
    ref = "Only the templater logger would see this"

    args = [
        '-i', input_file,
        '--dry_run',
        '-v'
        ]

    outstring = io.StringIO()
    with redirect_stdout(outstring):
        print("Test templater with logger decorator")
        templater.set_template(args)
        print("Test calling templater logging object")
        log = logging.getLogger('uwtools.templater')
        log.debug(ref)
    result = outstring.getvalue()

    assert ref in result
