"""
This file contains the specific drivers for a particular app, using the facade pattern base class.
"""

import logging
import shutil
import subprocess

from uwtools.drivers.facade import Facade
from uwtools.utils.cli_helpers import get_file_type


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
        if file_type == "INI":
            with open("config.yaml", "w", encoding="utf-8") as file:
                # Note: This is a temporary path until parsing the SRW directory is implemented.
                subprocess.run(
                    f"python config_utils.py -c {config_file} -t $PWD/config_defaults.yaml -o yaml",
                    capture_output=True,
                    check=False,
                    shell=True,
                    stdout=file,
                )
        elif file_type == "YAML":
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
        subprocess.run("python generate_FV3LAM_wflow.py", check=False, shell=True)

    def create_manager_files(self) -> None:
        """
        Create the manager files.
        """

    def link_fix_files(self) -> None:
        """
        Link the fix files.
        """
