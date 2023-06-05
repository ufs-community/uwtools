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
from uwtools.drivers.driver import Driver
from uwtools.drivers.forecast import FV3Forecast

uwtools_file_base = os.path.join(os.path.dirname(__file__))


def test_create_namelist():
    """Tests create_namelist method with and without optional base file"""
    forecast_obj = FV3Forecast(Driver)

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

        file = open(outnml_file, "r")
        outnml_string = file.read()

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

        file = open(outnml_file, "r")
        outnml_string = file.read()

        assert outnml_string == outcome2


def test_create_directory_structure():
    """Tests create_directory_structure method given a directory."""
    forecast_obj = FV3Forecast(Driver)

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
