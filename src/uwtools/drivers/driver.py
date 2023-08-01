"""
This file contains the scaffolding for the forecast driver. It is a Python script that will be
called by the user to run the forecast. It will call the other tools in the uwtools package to do
the work. It will also be responsible for setting up the working directory and moving files around.

See UW documentation for more information:
https://github.com/ufs-community/workflow-tools/wiki/Migrating-Production-Workflows-to-the-Unified-Workflow-using-the-Strangler-Fig-Pattern#component-drivers
"""

from abc import ABC, abstractmethod
from typing import Optional

from uwtools import config_validator
from uwtools.logger import Logger


class Driver(ABC):
    """
    This base class provides the interface to methods used to read in a user-provided YAML
    configuration file, convert it to the required config file, fix files, and namelist for a
    forecast. Subsequent methods will be used to stage the input files and run the forecast.

    Attributes
    ----------
    config_path : Path
        The file path to the configuration file to be parsed.

    Methods
    -------
    requirements()
        Recursively parse config and platform files to determine and
        fill in any dependencies.

    resources()
        Determine necessary task objects and fill in resource requirements of each.
        Returns a Config object containing the HPC resources needed.

    validate()
        Validates the objects generated by the driver from the provided
        config and platform files. If the --dry-run flag is provided, complete all
        stages through validation and print results without running the forecast.


    output()
        Holds the knowledge for how to modify a list of output files and
        stages them in the working directory.

    job_card()
        Turns the resources config object into a batch card for the
        configured Task. Can be called from the command line on the front end
        node to show the user what the job card would have looked like.

    Notes
    -------
    Several functions such as create_model_config() and run() are relegated to
    specific forecast drivers. This is because they are unique to the app being
    run and will appropriately parse subsequent stages of the workflow.
    """

    def __init__(self, config_file: Optional[str] = None):
        """
        Initialize the Forecast driver.
        """
        if config_file is not None:
            self.config = config_file
            self.validate()

    def validate(self, log: Optional[Logger] = None) -> bool:
        """
        Validates the objects generated by the driver from the provided config and platform files.

        If the --dry-run flag is provided, complete all stages through validation and print results
        without running the forecast.
        """

        log = Logger() if log is None else log
        return config_validator.config_is_valid(
            config_file=self.config,
            validation_schema=self.schema,
            log=log,
        )

    @property
    @abstractmethod
    def schema(self):
        """
        The schema to validate the config file against.
        """

    @abstractmethod
    def requirements(self):
        """
        Recursively parse config and platform files to determine and fill in any dependencies.
        """

    @abstractmethod
    def resources(self):
        """
        Determine necessary task objects and fill in resource requirements of each.

        Returns a Config object containing the HPC resources needed.
        """

    @abstractmethod
    def output(self):
        """
        Holds the knowledge for how to modify a list of output files and stages them in the working
        directory.

        Output files usually are specific to a given app.
        """

    @abstractmethod
    def job_card(self):
        """
        Turns the resources config object into a batch card for the configured Task.

        Can be called from the command line on the front end node to show the user what the job card
        would have looked like.
        """
