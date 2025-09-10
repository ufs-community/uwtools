"""
A base class for MPAS drivers.
"""

from __future__ import annotations

import re
from abc import abstractmethod
from datetime import datetime, timezone
from functools import reduce
from itertools import islice
from typing import TYPE_CHECKING, cast

from dateutil.relativedelta import relativedelta
from iotaa import asset, task, tasks
from lxml import etree
from lxml.etree import Element, SubElement

from uwtools.drivers.driver import DriverCycleBased
from uwtools.drivers.stager import FileStager

if TYPE_CHECKING:
    from pathlib import Path


class MPASBase(DriverCycleBased, FileStager):
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

    @abstractmethod
    def namelist_file(self):
        """
        The namelist file.
        """

    @tasks
    @abstractmethod
    def provisioned_rundir(self):
        """
        Run directory provisioned with all required content.
        """

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
                "filename_interval",
                "input_interval",
                "io_type",
                "output_interval",
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
        path.write_text(xml)

    # Public helper methods

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
            template = stream["filename_template"]
            if filename_interval == "none":
                paths.append(self._output_path(template, self._cycle))
            elif filename_interval in ("input_interval", "output_interval"):
                interval = stream[filename_interval]
                if interval == "none":
                    continue  # stream will not be written
                if interval == "initial_only":
                    paths.append(self._output_path(template, self._cycle))
                else:  # interval is a timestamp
                    tss = self._interval_timestamps(interval)
                    paths.extend(self._output_path(template, ts) for ts in tss)
            else:  # filename_interval is a timestamp
                reference_time = stream.get("reference_time")
                tss = self._filename_interval_timestamps(filename_interval, reference_time)
                paths.extend(self._output_path(template, ts) for ts in tss)
        return {"paths": sorted(set(paths))}

    # Private helper methods

    @staticmethod
    def _decode_interval(interval: str) -> dict[str, int]:
        # See MPAS User Guide section 5 in re: interval format and semantics, but the general form
        # is years-months-days_hours:minutes:seconds, e.g. 1-2-3_4:5:6 means 1 year, 2 months, 3
        # days, 4 hours, 5 minutes, 6 seconds. Leading components can be omitted, so reverse for an
        # ascending seconds -> years order, pad with trailing zeros as needed, then reverse again
        # for a natural descending years -> seconds order.
        keys = ["years", "months", "days", "hours", "minutes", "seconds"]
        components = re.sub(r"[-_:]", " ", interval).split()[::-1]
        vals = [next(islice(components, i, i + 1), 0) for i in range(len(keys))][::-1]
        return dict(zip(keys, map(int, vals)))

    @staticmethod
    def _decode_timestamp(timestamp: str) -> datetime:
        return datetime.strptime(timestamp, "%Y-%m-%d_%H:%M:%S").replace(tzinfo=timezone.utc)

    @staticmethod
    def _filename_interval(stream: dict) -> str:
        # See MPAS User Guide section 5.2 in re: filename_interval logic.
        assert stream["type"] in ("output", "input;output")
        filename_interval = "output_interval"
        if stream["type"] == "input;output" and stream["input_interval"] != "initial_only":
            filename_interval = "input_interval"
        return cast(str, stream.get("filename_interval", filename_interval))

    def _filename_interval_timestamps(
        self, interval: str, reference_time: str | None
    ) -> list[datetime]:
        # See MPAS User Guide sections 5.2 and 5.3.3 in re: the semantics of reference_time.
        # First, create a timestamp for each expected output file, per the timestamp-pattern value
        # of filename_interval. By default, the first timestamp will match the model start time, but
        # reference_time, if present, shifts it to a different time. In this case, the number of
        # output files does not change, but their timestamps and contents do.
        tss = self._interval_timestamps(interval)
        if reference_time:
            initial_ts, _ = self._initial_and_final_ts
            delta = initial_ts - self._decode_timestamp(reference_time)
            tss = [ts - delta for ts in tss]
        return tss

    @property
    @abstractmethod
    def _initial_and_final_ts(self) -> tuple[datetime, datetime]: ...

    def _interval_timestamps(self, interval: str) -> list[datetime]:
        kwargs = self._decode_interval(interval)
        delta = relativedelta(**kwargs)  # type: ignore[arg-type]
        ts, final_ts = self._initial_and_final_ts
        tss = []
        while ts <= final_ts:
            tss.append(ts)
            ts = ts + delta
        return tss

    def _output_path(self, template: str, dtobj: datetime) -> Path:
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
        template = reduce(lambda m, e: m.replace(e[0], e[1]), kvs, template)
        return self.rundir / dtobj.strftime(template)

    @property
    @abstractmethod
    def _streams_fn(self) -> str:
        """
        The streams filename.
        """
