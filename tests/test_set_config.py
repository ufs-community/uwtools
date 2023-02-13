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
        

def test_set_config_yaml_simple ():
    ''' Test that providing a YAML base file with necessary settings 
    will create a YAML config file'''

    # get input file
    input_file = os.path.join(uwtools_file_base, pathlib.Path("fixtures/simple2.yaml"))
    # create a temporary directory for outfile and expected file
    with tempfile.TemporaryDirectory(dir='.') as tmp_dir:
        # set outfile in temp directory
        out_file = f'{tmp_dir}/test_config_from_yaml.yaml'
        # create args for create_config_obj input
        args = ['-i', input_file, '-o', out_file]
        # create config obj from commandline inputs
        set_config.create_config_obj(args)
        # create expected file using config.py
        expected = config.YAMLConfig(input_file)
        expected_file = f'{tmp_dir}/expected_yaml.yaml'
        expected.dump_file(expected_file)
        
        # compare outfile and expected file
        assert compare_files(expected_file, out_file)
    
def test_set_config_ini_simple ():
    ''' Test that providing a basic INI file with necessary settings 
    will create an INI config file'''

    #get input file 
    input_file = os.path.join(uwtools_file_base, pathlib.Path("fixtures/simple.ini"))
    # create a temp directory for outfile and expected file
    with tempfile.TemporaryDirectory(dir='.') as tmp_dr:
        out_file = f'{tmp_dr}/test_config_from_ini.ini'
        args = ['-i', input_file, '-o', out_file]

        set_config.create_config_obj(args)

        expected = config.INIConfig(input_file)
        expected_file = f'{tmp_dr}/expected_ini.ini'
        expected.dump_file(expected_file)

        assert compare_files(expected_file, out_file)

def test_set_config_f90nml_simple ():
    '''Test that providing basic f90nml file with necessary settings
    will create f90nml config file'''

    input_file = os.path.join(uwtools_file_base, pathlib.Path("fixtures/simple.nml"))

    with tempfile.TemporaryDirectory(dir='.') as tmp_dr:

        out_file = f'{tmp_dr}/test_config_from_nml.nml'
        args = ['-i', input_file, '-o', out_file]

        set_config.create_config_obj(args)

        expected = config.F90Config(input_file)
        expected_file = f'{tmp_dr}/expected_nml.nml'
        expected.dump_file(expected_file)

        assert compare_files(expected_file, out_file)

def test_set_config_bash_simple ():
    '''Test that providing bash file with necessary settings will 
    create an INI config file'''

    input_file = os.path.join(uwtools_file_base, pathlib.Path("fixtures/simple.sh"))

    with tempfile.TemporaryDirectory(dir='.') as tmp_dr:

        out_file = f'{tmp_dr}/test_config_from_bash.ini'

        args = ['-i', input_file, '-o', out_file]

        set_config.create_config_obj(args)

        expected = config.INIConfig(input_file)
        expected_file = f'{tmp_dr}/expected_ini.ini'
        expected.dump_file(expected_file)

        assert compare_files(expected_file, out_file)

def test_set_config_yaml_config_file ():
    '''Test that providing a yaml base input file and a config file will
    create and update yaml config file'''

    input_file = os.path.join(uwtools_file_base, pathlib.Path("fixtures/fruit_config.yaml"))
    config_file = os.path.join(uwtools_file_base, pathlib.Path("fixtures/fruit_config_similar.yaml"))

    with tempfile.TemporaryDirectory(dir='.') as tmp_dir:

        out_file = f'{tmp_dir}/test_config_from_yaml.yaml'
        args = ['-i', input_file, '-o', out_file, '-c', config_file]
   
        set_config.create_config_obj(args)

        expected = config.YAMLConfig(input_file)
        config_file_obj = config.YAMLConfig(config_file)
        expected.update_values(config_file_obj)
        expected_file = f'{tmp_dir}/expected_yaml.yaml'
        expected.dump_file(expected_file)

        assert compare_files(expected_file, out_file)

def test_set_config_f90nml_config_file ():
    '''Test that providing a F90nml base input file and a config file will
    create and update F90nml config file'''

    input_file = os.path.join(uwtools_file_base, pathlib.Path("fixtures/simple.nml"))
    config_file = os.path.join(uwtools_file_base, pathlib.Path("fixtures/simple2.nml"))

    with tempfile.TemporaryDirectory(dir='.') as tmp_dir:

        out_file = f'{tmp_dir}/test_config_from_nml.nml'
        args = ['-i', input_file, '-o', out_file, '-c', config_file]
   
        set_config.create_config_obj(args)

        expected = config.F90Config(input_file)
        config_file_obj = config.F90Config(config_file)
        expected.update_values(config_file_obj)
        expected_file = f'{tmp_dir}/expected_nml.nml'
        expected.dump_file(expected_file)

        assert compare_files(expected_file, out_file)

def test_set_config_ini_config_file ():
    '''Test that aproviding INI base input file and a config file will 
    create and update INI config file'''

    input_file = os.path.join(uwtools_file_base, pathlib.Path("fixtures/simple.ini"))
    # config using bash file
    config_file = os.path.join(uwtools_file_base, pathlib.Path("fixtures/simple2.ini"))

    with tempfile.TemporaryDirectory(dir='.') as tmp_dir:

        out_file = f'{tmp_dir}/test_config_from_ini.ini'
        args = ['-i', input_file, '-o', out_file, '-c', config_file]
   
        set_config.create_config_obj(args)

        expected = config.INIConfig(input_file)
        config_file_obj = config.INIConfig(config_file)
        expected.update_values(config_file_obj)
        expected_file = f'{tmp_dir}/expected_ini.ini'
        expected.dump_file(expected_file)

        assert compare_files(expected_file, out_file)

def test_set_config_ini_bash_config_file ():
    '''Test that aproviding INI base input file and a config file will 
    create and update INI config file'''

    input_file = os.path.join(uwtools_file_base, pathlib.Path("fixtures/simple.ini"))
    # config using bash file
    config_file = os.path.join(uwtools_file_base, pathlib.Path("fixtures/fruit_config.sh"))

    with tempfile.TemporaryDirectory(dir='.') as tmp_dir:

        out_file = f'{tmp_dir}/test_config_from_ini.ini'
        args = ['-i', input_file, '-o', out_file, '-c', config_file]
   
        set_config.create_config_obj(args)

        expected = config.INIConfig(input_file)
        config_file_obj = config.INIConfig(config_file)
        expected.update_values(config_file_obj)
        expected_file = f'{tmp_dir}/expected_ini.ini'
        expected.dump_file(expected_file)

        assert compare_files(expected_file, out_file)



# questions
# how does it handle when no outfile provided?  how do we test for that?
