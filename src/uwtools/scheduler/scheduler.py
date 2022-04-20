from abc import ABC, abstractmethod
import collections
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from uwtools.scheduler import slurm

REQUIRED_OPTIONS: List[str] = []

FLAGS: Dict[Any, Any] = {}

Directives = List


class Scheduler(ABC):
    TYPE = None
    _MAP_SCHEDULER = {"slurm": slurm.Slurm, object: None}

    def __init__(self, **kwargs):
        self._props = kwargs

    def __getattr__(self, name):
        if name in self.props:
            return self.props[name]

    def __getitem__(self, key):
        return getattr(self, key)

    def __repr__(self):
        pass

    def __str__():
        pass

    @property
    def content(self):
        pass

    @classmethod
    def get_scheduler(cls, props):
        return cls._MAP_SCHEDULER[props.scheduler](props)

    def add_native_flag(self, flag):
        self.directives.append(self.native_flags)

    def _create_directive_list(self: list):

        """Uses the map_flags dict from subclass to build a directives list."""
        # Add in dict logic from PR comment here.
        raise NotImplementedError

    @abstractmethod
    def join_output(self):

        """Different schedulers handle the joining of output by removal
        of flags and/or the addition of other flags. PBS, for example,
        requires the addition of "-j oe" to join output, and Slurm
        requires that only the -o flag is provided."""
        pass

    @property
    def directives(self):
        ret = self._create_directive_list()
        if self.native_flags:
            self.add_native_flag()

        if self.join:
            self.join_output()
        return ret

    def write_job_card(self):

        with open(self.job_card_path) as fn:
            fn.write(self.directives.join("\n"))
            fn.write(self.run_command)
