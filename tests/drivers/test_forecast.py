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

def test_create_forecast_obj():
    ''' Tests stage files given config object'''

    with tempfile.TemporaryDirectory() as run_directory:
        config_dict = {
            "working_dir": f"./{run_directory}",
            "static": {},
            "cycledep": {},
        }
        forecast_obj = FV3Forecast(config_dict)

        # convert to config_obj?
        # perhaps wrong direction with uwtools_file_base? (taken from test_config)
        test_yaml = os.path.join(uwtools_file_base,pathlib.Path("./expt_dir.yaml"))
        test_cfg = config.YAMLConfig(test_yaml)
        # how to connect expt_dir and config_dict?
        forecast_obj.config_obj = test_cfg

        forecast_obj.create_directory_structure(run_directory)
        forecast_obj.stage_fix_files()

        # assert files have been staged / are in tmpdir
        # how to access files from aws?
        # test_file = os.path.join(run_directory, "co2historicaldata_2010.txt")
        # assert os.path.isfile(test_file)
        assert "co2historicaldata_2010.txt" in forecast_obj.config_obj

        # assert missing file is unavailable
        # test_file = os.path.join(run_directory, "bad_file.txt")
        # assert not os.path.isfile(test_file)
        assert not "bad_file.txt" in forecast_obj.config_obj

        forecast_obj.cycledep_files()

        # test_file = os.path.join(run_directory, "INPUT/gfs_data.nc")
        # assert os.path.isfile(test_file)
        assert "gfs_data.nc" in forecast_obj.config_obj["INPUT"]
