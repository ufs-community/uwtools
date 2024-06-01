"""
A base class for MPAS drivers.
"""

from abc import abstractmethod
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from iotaa import asset, task, tasks
from lxml import etree
from lxml.etree import Element, SubElement

from uwtools.drivers.driver import Driver
from uwtools.utils.tasks import filecopy, symlink


class MPASBase(Driver):
    """
    A base class for MPAS drivers.
    """

    def __init__(
        self,
        cycle: datetime,
        config: Optional[Path] = None,
        dry_run: bool = False,
        batch: bool = False,
        key_path: Optional[List[str]] = None,
    ):
        """
        The driver.

        :param config_file: Path to config file (read stdin if missing or None).
        :param cycle: The cycle.
        :param dry_run: Run in dry-run mode?
        :param batch: Run component via the batch system?
        :param key_path: Keys leading through the config to the driver's configuration block.
        """
        super().__init__(
            config=config, cycle=cycle, dry_run=dry_run, batch=batch, key_path=key_path
        )
        self._cycle = cycle

    # Workflow tasks

    @tasks
    @abstractmethod
    def boundary_files(self):
        """
        Boundary files.
        """

    @tasks
    def files_copied(self):
        """
        Files copied for run.
        """
        yield self._taskname("files copied")
        yield [
            filecopy(src=Path(src), dst=self._rundir / dst)
            for dst, src in self._driver_config.get("files_to_copy", {}).items()
        ]

    @tasks
    def files_linked(self):
        """
        Files linked for run.
        """
        yield self._taskname("files linked")
        yield [
            symlink(target=Path(target), linkname=self._rundir / linkname)
            for linkname, target in self._driver_config.get("files_to_link", {}).items()
        ]

    @task
    @abstractmethod
    def namelist_file(self):
        """
        The namelist file.
        """

    @tasks
    def provisioned_run_directory(self):
        """
        Run directory provisioned with all required content.
        """
        yield self._taskname("provisioned run directory")
        yield [
            self.boundary_files(),
            self.files_copied(),
            self.files_linked(),
            self.namelist_file(),
            self.runscript(),
            self.streams_file(),
        ]

    @task
    def runscript(self):
        """
        The runscript.
        """
        path = self._runscript_path
        yield self._taskname(path.name)
        yield asset(path, path.is_file)
        yield None
        self._write_runscript(path=path, envvars={})

    @task
    def streams_file(self):
        """
        The streams file.
        """
        fn = self._streams_fn
        yield self._taskname(fn)
        path = self._rundir / fn
        yield asset(path, path.is_file)
        yield None
        streams = Element("streams")
        for item in self._driver_config["streams"]:
            stream = SubElement(streams, "stream" if item["mutable"] else "immutable_stream")
            for attr in ["name", "type", "filename_template"]:
                stream.set(attr, item[attr])
            for attr in ["input_interval", "output_interval", "filename_interval", "packages"]:
                if attr in item:
                    stream.set(attr, item[attr])
            if files := item.get("files"):
                for file in files:
                    SubElement(stream, "file", name=file)
        path.parent.mkdir(parents=True, exist_ok=True)
        xml = etree.tostring(streams, pretty_print=True, encoding="utf-8").decode()
        with open(path, "w", encoding="utf-8") as f:
            f.write(xml)

    # Private helper methods

    @property
    @abstractmethod
    def _driver_name(self) -> str:
        """
        Returns the name of this driver.
        """

    @property
    @abstractmethod
    def _streams_fn(self) -> str:
        """
        The streams filename.
        """

    def _taskname(self, suffix: str) -> str:
        """
        Returns a common tag for graph-task log messages.

        :param suffix: Log-string suffix.
        """
        return self._taskname_with_cycle(self._cycle, suffix)
