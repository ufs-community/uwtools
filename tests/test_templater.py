#pylint: disable=unused-variable
"""
Tests for templater tool.
"""
from contextlib import redirect_stdout
import argparse
import filecmp
import io
import os
import tempfile

import pytest

from uwtools import templater

uwtools_file_base = os.path.join(os.path.dirname(__file__))

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

    outcome=\
"""&salad
    base = 'kale'
    fruit = 'banana'
    vegetable = 'tomato'
    how_many = 'much'
    dressing = 'balsamic'
/
"""
    os.environ['fruit'] = 'banana'
    os.environ['vegetable'] = 'tomato'
    os.environ['how_many'] = 'much'

    input_file = os.path.join(uwtools_file_base, "fixtures/nml.IN")

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

    outcome=\
'''Values needed for this template are:
fruit
how_many
vegetable
'''
    input_file = os.path.join(uwtools_file_base, "fixtures/nml.IN")

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

        assert filecmp.cmp(expected_file, out_file)
