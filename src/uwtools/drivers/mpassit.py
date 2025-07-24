"""
A driver for the MPASSIT component.
"""

from __future__ import annotations

import re
from abc import abstractmethod
from datetime import datetime, timezone
from functools import reduce
from itertools import islice
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import cast

from dateutil.relativedelta import relativedelta
from iotaa import asset, task, tasks
from lxml import etree
from lxml.etree import Element, SubElement

from uwtools.drivers.driver import DriverCycleBased
from uwtools.utils.tasks import filecopy, symlink


class MPASSIT(DriverCycleBased):
    """
    A driver for MPASSIT.
    """

    # Workflow tasks

    @tasks
    def files_copied(self):
        """
        Files copied for run.
        """
        yield self.taskname("files copied")
        yield [
            filecopy(src=Path(src), dst=self.rundir / dst)
            for dst, src in self.config.get("files_to_copy", {}).items()
        ]

    @tasks
    def files_linked(self):
        """
        Files linked for run.
        """
        yield self.taskname("files linked")
        yield [
            symlink(target=Path(target), linkname=self.rundir / linkname)
            for linkname, target in self.config.get("files_to_link", {}).items()
        ]

    @task
    def namelist_file(self):
        """
        The namelist file.
        """
        fn = "mpassit.namelist"
        yield self.taskname(fn)
        path = slef.rundir / fn
        yield asset(path, path.is_file)
        base_file = self.config[STR.namelist].get(STR.basefile)
        yield file(Path(base_file)) if base_file else None
        self.create_user_updated_config(
            config_class=NMLConfig,
            config_values=self.config[STR.namelist],
            path=path,
            schema=self.namelist_schema(),
        )

    @tasks
    def provisioned_rundir(self):
        """
        Run directory provisioned with all required content.
        """
        yield self.taskname("provisioned run directory")
        yield [
            self.files_copied(),
            self.files_linked(),
            self.namelist_file(),
            self.runscript(),
        ]

    # Public helper methods

    @property
    def output(self) -> str:
        """
        Returns a description of the file(s) created when this component runs.
        """
        with NamedTemporaryFile() as path:
            base_file = self.config[STR.namelist].get(STR.basefile)
            self.create_user_updated_config(
                config_class=NMLConfig,
                config_values=self.config[STR.namelist],
                path=path,
                schema=self.namelist_schema(),
            )
            namelist = get_nml_config(path)
        return namelist["config"]["output_file"]

