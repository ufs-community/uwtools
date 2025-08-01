"""
A driver for the ungrib component.
"""

from __future__ import annotations

from datetime import timedelta
from functools import cached_property
from pathlib import Path

from iotaa import asset, task, tasks

from uwtools.config.formats.nml import NMLConfig
from uwtools.drivers.driver import DriverCycleBased
from uwtools.drivers.support import set_driver_docstring
from uwtools.exceptions import UWConfigError
from uwtools.strings import STR
from uwtools.utils.processing import run_shell_cmd
from uwtools.utils.tasks import file
from uwtools.utils.time import to_datetime, to_iso8601, to_timedelta


class Ungrib(DriverCycleBased):
    """
    A driver for ungrib.
    """

    PREFIX = "FILE"

    # Workflow tasks

    @tasks
    def gribfiles(self):
        """
        Symlinks to all the GRIB files.
        """
        yield self.taskname("GRIB files")
        files = [Path(p) for p in self.config["gribfiles"]]
        yield [
            self._gribfile(src, self.rundir / f"GRIBFILE.{_ext(i)}") for i, src in enumerate(files)
        ]

    @task
    def namelist_file(self):
        """
        The namelist file.
        """
        fmttime = lambda key: to_datetime(self.config[key]).strftime("%Y-%m-%d_%H:00:00")
        d = {
            "update_values": {
                "share": {
                    "end_date": fmttime("stop"),
                    "interval_seconds": int(self._step.total_seconds()),
                    "max_dom": 1,
                    "start_date": fmttime("start"),
                    "wrf_core": "ARW",
                },
                "ungrib": {
                    "out_format": "WPS",
                    "prefix": self.PREFIX,
                },
            }
        }
        path = self.rundir / "namelist.wps"
        yield self.taskname(str(path))
        yield asset(path, path.is_file)
        yield None
        self.create_user_updated_config(
            config_class=NMLConfig,
            config_values=d,
            path=path,
        )

    @tasks
    def provisioned_rundir(self):
        """
        Run directory provisioned with all required content.
        """
        yield self.taskname("provisioned run directory")
        yield [
            self.gribfiles(),
            self.namelist_file(),
            self.runscript(),
            self.vtable(),
        ]

    @task
    def vtable(self):
        """
        A symlink to the Vtable file.
        """
        path = self.rundir / "Vtable"
        yield self.taskname(str(path))
        yield asset(path, path.is_symlink)
        infile = Path(self.config["vtable"])
        yield file(path=infile)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.symlink_to(Path(self.config["vtable"]))

    @task
    def _run_via_local_execution(self):
        """
        A run executed directly on the local system.
        """
        yield self.taskname("run via local execution")
        yield [asset(path, path.is_file) for path in self.output["paths"]]
        yield self.provisioned_rundir()
        cmd = "{x} >{x}.out 2>&1".format(x=self._runscript_path)
        run_shell_cmd(cmd=cmd, cwd=self.rundir, log_output=True)

    # Public helper methods

    @classmethod
    def driver_name(cls) -> str:
        """
        The name of this driver.
        """
        return STR.ungrib

    @property
    def output(self) -> dict[str, list[Path]]:
        """
        Returns a description of the file(s) created when this component runs.
        """
        bounds: list[str] = [self.config[x] for x in ("start", "stop")]
        start, stop = map(to_datetime, bounds)
        if stop < start:
            msg = "Value 'stop' (%s) precedes 'start' (%s)" % tuple(map(to_iso8601, [stop, start]))
            raise UWConfigError(msg)
        increment = int(self._step.total_seconds())
        current = start
        paths = []
        while current <= stop:
            fn = "%s:%s" % (self.PREFIX, current.strftime("%Y-%m-%d_%H"))
            paths.append(self.rundir / fn)
            if increment == 0:
                break
            current += timedelta(seconds=increment)
        return {"paths": paths}

    # Private helper methods

    @task
    def _gribfile(self, infile: Path, link: Path):
        """
        A symlink to an input GRIB file.

        :param link: Link name.
        :param infile: File to link.
        """
        yield self.taskname(str(link))
        yield asset(link, link.is_symlink)
        yield file(path=infile)
        link.parent.mkdir(parents=True, exist_ok=True)
        link.symlink_to(infile)

    @cached_property
    def _step(self) -> timedelta:
        td = to_timedelta(self.config["step"])
        if (val := int(td.total_seconds())) < 0:
            raise UWConfigError("Value for 'step' (%s seconds) should be non-negative" % val)
        return td


def _ext(n: int) -> str:
    """
    Return a 3-letter representation of the given integer.

    :param n: The integer to convert to a string representation.
    """
    b = 26
    return "{:A>3}".format(("" if n < b else _ext(n // b)) + chr(65 + n % b))[-3:]


set_driver_docstring(Ungrib)
