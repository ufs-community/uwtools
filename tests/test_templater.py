"""
Tests for templater tool.
"""
import argparse
from contextlib import redirect_stdout
import io
import os
import shutil
import tempfile

import pytest

from scripts import templater
from uwtools.utils import file_helpers

uwtools_file_base = os.path.join(os.path.dirname(__file__))


def test_set_template_dryrun(): #pylint: disable=unused-variable
    """Unit test for checking dry-run output of ingest namelist tool"""

    input_file = os.path.join(uwtools_file_base, "fixtures/nml.IN")
    outcome=\
    f"""Running set_template with args:
----------------------------------------------------------------------
----------------------------------------------------------------------
        outfile: None
 input_template: {input_file}
    config_file: None
   config_items: []
        dry_run: True
  values_needed: False
        verbose: False
          quiet: False

re-run settings: templater.py  -i {input_file} --dry_run
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

    for outcome_line in outcome.split('\n'):
        assert outcome_line in result

def test_set_template_listvalues(): #pylint: disable=unused-variable
    """Unit test for checking values_needed output of ingest namelist tool"""

    input_file = os.path.join(uwtools_file_base, "fixtures/nml.IN")

    outcome=\
    f"""Running set_template with args:
----------------------------------------------------------------------
----------------------------------------------------------------------
        outfile: None
 input_template: {input_file}
    config_file: None
   config_items: []
        dry_run: False
  values_needed: True
        verbose: False
          quiet: False

re-run settings: templater.py  -i {input_file} --values_needed
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

    for outcome_line in outcome.split('\n'):
        assert outcome_line in result

def test_set_template_yaml_config(): #pylint: disable=unused-variable
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
        assert file_helpers.compare_files(expected_file, out_file)

def test_set_template_no_config_suffix_fails(): #pylint: disable=unused-variable

    ''' Test that there are no errors when passing relative path and INI
    config.'''

    input_file = "tests/fixtures/nml.IN"
    config_file = "tests/fixtures/fruit_config.sh"

    with tempfile.NamedTemporaryFile(dir='.', mode='w') as tmp_file:
        shutil.copy2(config_file, tmp_file.name)

        args = [
            '-i', input_file,
            '-c', tmp_file.name,
            '-d',
            ]
        with pytest.raises(ValueError):
            templater.set_template(args)

def test_set_template_abs_path_ini_config(): #pylint: disable=unused-variable

    ''' Test that there are no errors when passing relative path and INI
    config.'''

    input_file = "tests/fixtures/nml.IN"
    config_file = "tests/fixtures/fruit_config.sh"

    args = [
         '-i', input_file,
         '-c', config_file,
         '-d',
         ]
    templater.set_template(args)

def test_set_template_command_line_config(): #pylint: disable=unused-variable
    '''Test that values provided on the command line produce the appropriate
    output.'''

    input_file = os.path.join(uwtools_file_base, "fixtures/nml.IN")

    outcome=\
    f"""Running set_template with args:
----------------------------------------------------------------------
----------------------------------------------------------------------
        outfile: None
 input_template: {input_file}
    config_file: None
   config_items: ['fruit=pear', 'vegetable=squash', 'how_many=22']
        dry_run: True
  values_needed: False
        verbose: False
          quiet: False

re-run settings: templater.py  -i {input_file} --dry_run fruit=pear vegetable=squash how_many=22
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
    for outcome_line in outcome.split('\n'):
        assert outcome_line in result

def test_set_template_yaml_config_model_configure(): #pylint: disable=unused-variable
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
        assert file_helpers.compare_files(expected_file, out_file)


def test_set_template_verbosity(): #pylint: disable=unused-variable
    """Unit test for checking dry-run output of ingest namelist tool"""

    input_file = os.path.join(uwtools_file_base, "fixtures/nml.IN")
    logfile = os.path.join(os.path.dirname(templater.__file__), "templater.log")

    outcome=\
    f"""Finished setting up debug file logging in {logfile}
Running set_template with args:
----------------------------------------------------------------------
----------------------------------------------------------------------
        outfile: None
 input_template: {input_file}
    config_file: None
   config_items: []
        dry_run: True
  values_needed: False
        verbose: True
          quiet: False
re-run settings: templater.py  -i {input_file} --dry_run -v
----------------------------------------------------------------------
----------------------------------------------------------------------
&salad
  base = 'kale'
  fruit = 'banana'
  vegetable = 'tomato'
  how_many = 22
  dressing = 'balsamic'
/
J2Template._load_file INPUT Args:
{input_file}
"""

    os.environ['fruit'] = 'banana'
    os.environ['how_many'] = '22'
    if os.environ.get("vegetable") is not None:
        del os.environ['vegetable']

    #test verbose level
    args = [
         '-i', input_file,
         '--dry_run',
         '-v',
         ]

    with pytest.raises(ValueError) as error:
        templater.set_template(args)

    expected = "Missing values needed by template"
    actual = str(error.value)
    assert expected == actual

    os.environ['vegetable'] = 'tomato'

    # Capture verbose stdout
    outstring = io.StringIO()
    with redirect_stdout(outstring):
        templater.set_template(args)
    result = outstring.getvalue()

    for outcome_line in outcome.split('\n'):
        assert outcome_line in result

    #test quiet level
    args = [
         '-i', input_file,
         '-q',
         ]

    with pytest.raises(argparse.ArgumentError):
        templater.set_template(args)

def test_mutually_exclusive_args(): #pylint: disable=unused-variable
    ''' Test that -q and -v args are mutually exclusive and testing -q and -d are mutually exclusive.'''

    input_file = os.path.join(uwtools_file_base, "fixtures/fruit_config.yaml")

    args = [
        '-i', input_file, 
        '-v', 
        '-q',
        ]

    with pytest.raises(SystemExit):
        templater.set_template(args)

    args = ['-i', input_file,
            '-d', 
            '-q',
            ]

    with pytest.raises(argparse.ArgumentError):
        templater.set_template(args)
