#pylint: disable=invalid-name, missing-module-docstring, missing-function-docstring
#pylint: disable=unused-variable

import os
import shutil

from uwtools.drivers.driver import Driver
from uwtools.drivers.forecast import FV3Forecast


def test_create_directory_structure():
    """Tests create_directory_structure method given a directory."""
    forecast_obj = FV3Forecast(Driver)
    uwtools_file_base = os.path.join(os.path.dirname(__file__))
    run_directory = os.path.join(uwtools_file_base, "expt_dir")

    forecast_obj.create_directory_structure(run_directory, "delete")
    assert os.path.isdir(os.path.join(run_directory, "RESTART"))

    shutil.rmtree(run_directory)
