'''
Tests for forecast driver
'''
#pylint: disable=unused-variable

import os
import pathlib
import shutil
import glob
import tempfile
import pytest

from uwtools import config
from uwtools.drivers.forecast import FV3Forecast

uwtools_file_base = os.path.join(os.path.dirname(__file__))


def compare_files(expected, actual):
    '''Compare the content of two files.  Doing this over filecmp.cmp since 
    we may not be able to handle end-of-file character differences with it.
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


def test_create_config():
    '''Test that providing a yaml base input file and a config file will
    create and update yaml config file'''
    input_file = os.path.join(uwtools_file_base, pathlib.Path("fixtures/fruit_config.yaml"))
    config_file = os.path.join(uwtools_file_base, pathlib.Path("fixtures/fruit_config_similar.yaml"))

    forecast_obj = FV3Forecast()

    with tempfile.TemporaryDirectory(dir='.') as tmp_dir:

        out_file = f'{tmp_dir}/test_config_from_yaml.yaml'

        forecast_obj.create_model_config(config_file, out_file, input_file)

        expected = config.YAMLConfig(input_file)
        config_file_obj = config.YAMLConfig(config_file)
        expected.update_values(config_file_obj)
        expected_file = f'{tmp_dir}/expected_yaml.yaml'
        expected.dump_file(expected_file)

        assert compare_files(expected_file, out_file)

def test_create_namelist():
    """Tests create_namelist method with and without optional base file"""
    forecast_obj = FV3Forecast()

    with tempfile.TemporaryDirectory() as run_directory:

        update_file = os.path.join(uwtools_file_base,
                                   pathlib.Path("../fixtures/simple.nml"))
        update_obj = config.F90Config(update_file)

        base_file = os.path.join(uwtools_file_base,
                                 pathlib.Path("../fixtures/simple3.nml"))

        file_out = 'create_out.nml'
        outnml_file = os.path.join(run_directory, file_out)

        outcome=\
        """&salad
    base = 'kale'
    fruit = 'banana'
    vegetable = 'tomato'
    how_many = 12
    dressing = 'balsamic'
/
"""

        forecast_obj.create_namelist(update_obj, outnml_file)

        with open(outnml_file, "r", encoding="utf-8") as out_file:
            outnml_string = out_file.read()

        assert outnml_string == outcome

        outcome2=\
        """&salad
    base = 'kale'
    fruit = 'banana'
    vegetable = 'tomato'
    how_many = 12
    dressing = 'balsamic'
    toppings = ,
    extras = 0
    dessert = .false.
    appetizer = ,
/
"""

        forecast_obj.create_namelist(update_obj, outnml_file, base_file)

        with open(outnml_file, "r", encoding="utf-8") as out_file:
            outnml_string = out_file.read()

        assert outnml_string == outcome2


def test_create_directory_structure():
    """Tests create_directory_structure method given a directory."""
    forecast_obj = FV3Forecast()

    with tempfile.TemporaryDirectory() as run_directory:
        # Test create_directory_structure when run directory does not exist
        forecast_obj.create_directory_structure(run_directory, "delete")
        assert os.path.isdir(os.path.join(run_directory, "RESTART"))

        # Put a test file into the run directory
        test_file = os.path.join(run_directory, "test.txt")
        with open(test_file, "w", encoding="utf-8") as file_open:
            file_open.write("test file")
            file_open.close()

        # Test create_directory_structure when run directory does exist
        forecast_obj.create_directory_structure(run_directory, "delete")
        assert os.path.isdir(os.path.join(run_directory, "RESTART"))
        # Test file should be gone after delete
        assert not os.path.isfile(test_file)

        # Test create_directory_structure when run directory does exist
        forecast_obj.create_directory_structure(run_directory, "rename")
        copy_directory = glob.glob(run_directory + "_*")[0]
        assert os.path.isdir(os.path.join(copy_directory, "RESTART"))

        # Clean up copied directory fronm rename
        if os.path.isdir(copy_directory):
            shutil.rmtree(copy_directory)

        # Test create_directory_structure when run directory does exist
        with pytest.raises(SystemExit) as pytest_wrapped_e:
            forecast_obj.create_directory_structure(run_directory, "quit")
        assert pytest_wrapped_e.type == SystemExit
        assert pytest_wrapped_e.value.code == 1
