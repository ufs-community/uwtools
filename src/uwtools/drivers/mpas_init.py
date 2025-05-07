"""
A driver for the MPAS Init component.
"""

import re
from datetime import datetime, timedelta, timezone
from functools import reduce
from itertools import islice
from pathlib import Path
from typing import cast

from dateutil.relativedelta import relativedelta
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

    @property
    def output(self) -> dict[str, list[Path]]:
        """
        Returns a description of the file(s) created when this component runs.
        """
        paths = []
        for stream in self.config["streams"].values():
            if stream["type"] not in ("output", "input;output"):
                continue
            filename_interval = self._filename_interval(stream)
            if filename_interval == "none":
                paths.append(self._path(stream, self._cycle))
            elif filename_interval in ("input_interval", "output_interval"):
                interval = stream[filename_interval]
                if interval == "none":
                    continue  # stream will not be written
                if interval == "initial_only":
                    paths.append(self._path(stream, self._cycle))
                else:  # interval is a timestamp
                    tss = self._interval_timestamps(interval)
                    paths.extend(self._path(stream, ts) for ts in tss)
            else:  # filename_interval is a timestamp
                tss = self._interval_timestamps(filename_interval)
                if reference_time := stream.get("reference_time"):
                    initial_ts, _ = self._initial_and_final_ts
                    delta = initial_ts - self._decode_timestamp(reference_time)
                    tss = [ts - delta for ts in tss]
                paths.extend(self._path(stream, ts) for ts in tss)
        return {"paths": sorted(set(paths))}

    # Private helper methods

    @staticmethod
    def _decode_interval(interval: str) -> dict[str, int]:
        val = lambda x: int(x) if x else 0
        parts = re.sub(r"[-_:]", " ", interval).split()[::-1]
        keys = ["years", "months", "days", "hours", "minutes", "seconds"]
        vals = [val(x) for x in (next(islice(parts, i, i + 1), None) for i in range(6))][::-1]
        return dict(zip(keys, vals))

    @staticmethod
    def _decode_timestamp(timestamp: str) -> datetime:
        return datetime.strptime(timestamp, "%Y-%m-%d_%H:%M:%S").replace(tzinfo=timezone.utc)

    @staticmethod
    def _filename_interval(stream: dict) -> str:
        # See MPAS User Guide section 5.2 in re: filename_interval logic.
        filename_interval = "output_interval"
        if stream["type"] == "input;output" and stream["input_interval"] != "initial_only":
            filename_interval = "input_interval"
        return cast(str, stream.get("filename_interval", filename_interval))

    @property
    def _initial_and_final_ts(self) -> tuple[datetime, datetime]:
        initial = self._cycle.replace(tzinfo=timezone.utc)
        final = initial + timedelta(hours=self.config["boundary_conditions"]["length"])
        return initial, final

    def _interval_timestamps(self, interval: str) -> list[datetime]:
        kwargs = self._decode_interval(interval)
        delta = relativedelta(**kwargs)  # type: ignore[arg-type]
        ts, final_ts = self._initial_and_final_ts
        tss = []
        while ts <= final_ts:
            tss.append(ts)
            ts = ts + delta
        return tss

    def _path(self, stream: dict, dtobj: datetime) -> Path:
        # See MPAS User Guide section 5.1 in re: filename_template logic.
        kvs = [
            ("$Y", "%Y"),
            ("$M", "%m"),
            ("$D", "%d"),
            ("$d", "%j"),
            ("$h", "%H"),
            ("$m", "%M"),
            ("$s", "%S"),
        ]
        template = reduce(lambda m, e: m.replace(e[0], e[1]), kvs, stream["filename_template"])
        return self.rundir / dtobj.strftime(template)

    @property
    def _streams_fn(self) -> str:
        """
        The streams filename.
        """
        return "streams.init_atmosphere"


set_driver_docstring(MPASInit)
