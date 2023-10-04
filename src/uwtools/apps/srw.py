"""
This file contains the specific drivers for a particular app, using the facade pattern base class.
"""

import logging
import shutil

from uwtools.drivers.facade import Facade
from uwtools.exceptions import UWError
from uwtools.utils.file import FORMAT, get_file_type
from uwtools.utils.processing import execute


class SRW210(Facade):
    """
    Concrete class to handle UFS Short Range Weather app forecasts.

    Methods call manual command line processes as described in the docs. UFS Short Range Weather
    app, release v2.1.0
    """

    def __init__(self):
        """
        Initialize the facade driver.
        """

    def load_config(self, config_file: str) -> None:
        """
        Load the configuration file.
        """
        file_type = get_file_type(config_file)
        if file_type == FORMAT.ini:
            with open("config.yaml", "w", encoding="utf-8") as f:
                # Note: This is a temporary path until parsing the SRW directory is implemented.
                cmd_components = [
                    "python config_utils.py",
                    "-c %s" % config_file,
                    "-t $PWD/config_defaults.yaml",
                    "-o yaml",
                    ">%s" % f,
                ]
                cmd = " ".join(cmd_components)
                result = execute(cmd=cmd)
                if not result.success:
                    raise UWError(f"Command failed: {cmd}")
        elif file_type == FORMAT.yaml:
            shutil.copy2(config_file, "config.yaml")
        else:
            msg = f"Bad file type -- {file_type}. Cannot load configuration!"
            logging.critical(msg)
            raise ValueError(msg)

    def validate_config(self, config_file: str) -> None:
        """
        Validate the configuration file.
        """

    def create_experiment(self) -> None:
        """
        Generate the regional workflow.

        This sets up the workflow based on config.yaml, links fix files, creates input.nml and
        FV3LAM_wflow.xml.
        """
        # Note: This is a temporary path until parsing the SRW directory is implemented.
        cmd = "python generate_FV3LAM_wflow.py"
        result = execute(cmd=cmd)
        if not result.success:
            raise UWError(f"Command failed: {cmd}")

    def create_manager_files(self) -> None:
        """
        Create the manager files.
        """

    def link_fix_files(self) -> None:
        """
        Link the fix files.
        """
