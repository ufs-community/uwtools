#pylint: disable=unused-variable

'''
Tests for set_config tool
'''
from contextlib import redirect_stdout
import argparse
import io
import pathlib
import os
import tempfile
import pytest
from uwtools import config
from uwtools import set_config


uwtools_file_base = os.path.join(os.path.dirname(__file__))

def compare_files(expected, actual):
    '''Compare the content of two files.  Doing this over filecmp.cmp since 
    we may not be able to handle end-of-file character differences with it.
    Prints the contents of two compared files to std out if they do not match.'''

    with open(expected, 'r', encoding='utf-8') as expected_file:
        expected_content = expected_file.read().rstrip('\n')
    with open (actual, 'r', encoding='utf-8') as actual_file:
        actual_content = actual_file.read().rstrip('\n')

    if expected_content != actual_content:
        print ('The expected file looks like:')
        print (expected_content)
        print ('*' * 80)
        print ('The rendered file looks like:')
        print (actual_content)
        return False
    return True

def test_path_if_file_exists():
    '''Make sure the function works as expected.  It is used as a type in 
    argparse, so raises an argparse exception when the user provides a 
    non-existant path.'''

    with tempfile.NamedTemporaryFile(dir='.', mode='w') as tmp_file:
        assert set_config.path_if_file_exists(tmp_file.name)

    with pytest.raises(argparse.ArgumentTypeError):
        not_a_filepath = './no_way_this_file_exists.nope'
        set_config.path_if_file_exists(not_a_filepath)
        

# test command line with input file
# seperate test for every file type

def test_set_config_yaml_simple ():
    ''' Test that providing a YAML base file with necessary settings 
    will create a YAML config file'''

    input_file = os.path.join(uwtools_file_base, pathlib.Path("fixtures/simple2.yaml"))
    with tempfile.TemporaryDirectory(dir='.') as tmp_dir:
        out_file = f'{tmp_dir}/test_config_from_yaml.yaml'
    

    args = ['-i', input_file, '-o', out_file]
    set_config.create_config_obj(args)
    expected_file = config.YAMLConfig(input_file)
    assert compare_files(expected_file, out_file)
    