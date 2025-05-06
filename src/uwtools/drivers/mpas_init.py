"""
A driver for the MPAS Init component.
"""

import re
from datetime import datetime, timedelta
from functools import reduce
from itertools import islice
from pathlib import Path
from types import SimpleNamespace as ns

from iotaa import asset, task, tasks

from uwtools.config.formats.nml import NMLConfig
from uwtools.drivers.mpas_base import MPASBase
from uwtools.drivers.support import set_driver_docstring
from uwtools.strings import STR
from uwtools.utils.tasks import file, symlink


class MPASInit(MPASBase):
    """
    A driver for MPAS Init.
    """

    # Workflow tasks

    @tasks
    def boundary_files(self):
        """
        Boundary files.
        """
        yield self.taskname("boundary files")
        bcs = self.config["boundary_conditions"]
        offset = abs(bcs["offset"])
        endhour = bcs["length"] + offset
        interval = bcs["interval_hours"]
        symlinks = {}
        boundary_filepath = bcs["path"]
        for boundary_hour in range(0, endhour + 1, interval):
            file_date = self._cycle + timedelta(hours=boundary_hour)
            fn = f"FILE:{file_date.strftime('%Y-%m-%d_%H')}"
            target = Path(boundary_filepath, fn)
            linkname = self.rundir / fn
            symlinks[target] = linkname
        yield [symlink(target=tgt, linkname=lnk) for tgt, lnk in symlinks.items()]

    @task
    def namelist_file(self):
        """
        The namelist file.
        """
        fn = "namelist.init_atmosphere"
        yield self.taskname(fn)
        path = self.rundir / fn
        yield asset(path, path.is_file)
        base_file = self.config[STR.namelist].get(STR.basefile)
        yield file(Path(base_file)) if base_file else None
        initial_ts, final_ts = self._initial_and_final_ts
        namelist = self.config[STR.namelist]
        update_values = namelist.get(STR.updatevalues, {})
        update_values.setdefault("nhyd_model", {}).update(
            {
                "config_start_time": initial_ts.strftime("%Y-%m-%d_%H:00:00"),
                "config_stop_time": final_ts.strftime("%Y-%m-%d_%H:00:00"),
            }
        )
        namelist[STR.updatevalues] = update_values
        self._create_user_updated_config(
            config_class=NMLConfig,
            config_values=namelist,
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
            self.boundary_files(),
            self.files_copied(),
            self.files_linked(),
            self.namelist_file(),
            self.runscript(),
            self.streams_file(),
        ]

    # Public helper methods

    @classmethod
    def driver_name(cls) -> str:
        """
        The name of this driver.
        """
        return STR.mpasinit

    # ruff: noqa: ERA001
    @property
    def output(self) -> dict[str, list[Path]]:
        """
        Returns a description of the file(s) created when this component runs.
        """
        kvs = [
            ("$Y", "%Y"),
            ("$M", "%m"),
            ("$D", "%d"),
            ("$d", "%j"),
            ("$h", "%H"),
            ("$m", "%M"),
            ("$s", "%S"),
        ]
        paths = []
        for stream in self.config["streams"].values():
            if stream["type"] not in ("output", "input;output"):
                continue
            # See MPAS User Guide section 5.1 in re: filename_template logic.
            template = reduce(lambda m, e: m.replace(e[0], e[1]), kvs, stream["filename_template"])
            path = lambda ts: self.rundir / ts.strftime(template)  # noqa: B023
            # See MPAS User Guide section 5.2 in re: filename_interval logic.
            filename_interval = "output_interval"
            if stream["type"] == "input;output" and stream["input_interval"] != "initial_only":
                filename_interval = "input_interval"
            filename_interval = stream.get("filename_interval", filename_interval)
            if filename_interval == "none":
                paths.append(path(self._cycle))
            elif filename_interval == "output_interval":
                interval = stream["output_interval"]
                if interval == "none":
                    continue
                if interval == "initial_only":
                    paths.append(path(self._cycle))
                else:
                    decoded = self._decode_interval(interval)
                    assert decoded
            elif filename_interval == "input_interval":
                raise NotImplementedError(2)
            else:  # timestamp pattern
                raise NotImplementedError(3)
        return {"paths": sorted(set(paths))}

    # Private helper methods

    @staticmethod
    def _decode_interval(interval: str) -> ns:
        val = lambda x: int(x) if x else None
        parts = re.sub(r"[-_:]", " ", interval).split()[::-1]
        keys = ["years", "months", "days", "hours", "minutes", "seconds"]
        vals = [val(x) for x in (next(islice(parts, i, i + 1), None) for i in range(6))][::-1]
        return ns(**dict(zip(keys, vals)))

    @property
    def _initial_and_final_ts(self) -> tuple[datetime, datetime]:
        initial = self._cycle
        final = initial + timedelta(hours=self.config["boundary_conditions"]["length"])
        return initial, final

    @property
    def _streams_fn(self) -> str:
        """
        The streams filename.
        """
        return "streams.init_atmosphere"


set_driver_docstring(MPASInit)
