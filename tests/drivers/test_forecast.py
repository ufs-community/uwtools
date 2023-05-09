#pylint: disable=invalid-name, missing-module-docstring, missing-function-docstring
#pylint: disable=unused-variable

import os
import shutil
import glob
import pytest

from uwtools.drivers.driver import Driver
from uwtools.drivers.forecast import FV3Forecast


def test_create_directory_structure():
    """Tests create_directory_structure method given a directory."""
    forecast_obj = FV3Forecast(Driver)
    uwtools_file_base = os.path.join(os.path.dirname(__file__))
    run_directory = os.path.join(uwtools_file_base, "expt_dir")
    if os.path.isdir(run_directory):
        shutil.rmtree(run_directory)

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

    # Test create_directory_structure when run directory does exist
    with pytest.raises(SystemExit) as pytest_wrapped_e:
        forecast_obj.create_directory_structure(run_directory, "quit")
    assert pytest_wrapped_e.type == SystemExit
    assert pytest_wrapped_e.value.code == 1

    # Clean up test directories
    if os.path.isdir(run_directory):
        shutil.rmtree(run_directory)
    if os.path.isdir(copy_directory):
        shutil.rmtree(copy_directory)
