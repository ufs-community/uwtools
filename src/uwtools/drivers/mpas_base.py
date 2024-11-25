"""
A base class for MPAS drivers.
"""

from abc import abstractmethod
from pathlib import Path

from iotaa import asset, task, tasks
from lxml import etree
from lxml.etree import Element, SubElement

from uwtools.drivers.driver import DriverCycleBased
from uwtools.utils.tasks import filecopy, symlink


class MPASBase(DriverCycleBased):
    """
    A base class for MPAS drivers.
    """

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
    @abstractmethod
    def namelist_file(self):
        """
        The namelist file.
        """

    @tasks
    def provisioned_rundir(self):
        """
        Run directory provisioned with all required content.
        """
        yield self.taskname("provisioned run directory")
        required = [
            self.files_copied(),
            self.files_linked(),
            self.namelist_file(),
            self.runscript(),
            self.streams_file(),
        ]
        if self.config["domain"] == "regional":
            required.append(self.boundary_files())
        yield required

    @task
    def streams_file(self):
        """
        The streams file.
        """
        fn = self._streams_fn
        yield self.taskname(fn)
        path = self.rundir / fn
        yield asset(path, path.is_file)
        yield None
        streams = Element("streams")
        for k, v in self.config["streams"].items():
            stream = SubElement(streams, "stream" if v["mutable"] else "immutable_stream")
            stream.set("name", k)
            for attr in ["type", "filename_template"]:
                stream.set(attr, v[attr])
            for attr in [
                "clobber_mode",
                "input_interval",
                "io_type",
                "output_interval",
                "filename_interval",
                "packages",
                "precision",
                "reference_time",
            ]:
                if attr in v:
                    stream.set(attr, v[attr])
            for elem in ("file", "stream", "var", "var_array", "var_struct"):
                if items := v.get(f"{elem}s"):
                    for item in items:
                        SubElement(stream, elem, name=item)
        path.parent.mkdir(parents=True, exist_ok=True)
        xml = etree.tostring(streams, pretty_print=True, encoding="utf-8").decode()
        with open(path, "w", encoding="utf-8") as f:
            f.write(xml)

    # Private helper methods

    @property
    @abstractmethod
    def _streams_fn(self) -> str:
        """
        The streams filename.
        """
