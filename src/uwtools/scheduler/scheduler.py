from abc import ABC, abstractmethod
import collections
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from uwtools.scheduler import slurm

REQUIRED_OPTIONS: List[str] = []

FLAGS: Dict[Any, Any] = {}


def create_directive_list(self, flags, specs):
    flags = list(
        [f"{self._DIRECTIVE} --{flag}={setting}" for (flag, setting) in flags.items()]
    )
    if "join" in specs:
        flags.append(f"{self._DIRECTIVE} --error {specs.join}")
    else:
        if "stdout" in specs:
            flags.append(f"{self._DIRECTIVE} --output {specs.stdout}")
        if "stderr" in specs:
            flags.append(f"{self._DIRECTIVE} --error {specs.stderr}")
    return "\n".join(flags)


class Directives(collections.UserList):
    def __init__(self, map_flags: Dict[str, str], specs):
        self.map_flags = map_flags
        self._DIRECTIVE = None
        self.append(
            [
                f"{self._DIRECTIVE} --{flag}={setting}"
                for (flag, setting) in map_flags.items()
            ]
        )

    @property
    def list(self):
        self.append(
            [
                f"{self._DIRECTIVE} --{flag}={setting}"
                for (flag, setting) in self.map_flags.items()
            ]
        )


MAP = {
    "slurm": slurm.Slurm,
}


class Scheduler(ABC):
    TYPE = None

    def __init__(self, props):
        self._props = props

    def __getattr__(self, name):
        if name in self.props:
            return self.props[name]

    def __getitem__(self, key):
        return getattr(self, key)

    @classmethod
    def get_scheduler(props) -> "Scheduler":

        return map[props.scheduler](props)


class Scheduler(ABC):
    def __init__(
        self,
        job_name: str,
        partition: list,
        qos: str,
        output: Path,
        error: Path,
        walltime: datetime,
        account: str,
        nodes: int,
        ntasks_per_node: int,
        ntasks: int,
        cpus_per_task: int,
        reservation: str,
        join: bool,
        native_flags: list,
        run_command: str,
        job_card_path: Path,
    ):
        self.scheduler = scheduler
        self.job_name = job_name
        self.partition = partition
        self.qos = qos
        self.output = output
        self.error = error
        self.walltime = walltime
        self.account = account
        self.nodes = nodes
        self.ntasks_per_node = ntasks_per_node
        self.ntasks = ntasks
        self.cpus_per_task = cpus_per_task
        self.reservation = reservation
        self.join = join
        self.native_flags = native_flags
        self.run_command = run_command
        self.job_card_path = job_card_path

    def add_native_flag(self, flag):
        self.directives.append(self.native_flags)

    def check_required_options(self):
        """Not sure what this thing does at this point."""
        pass

    def _create_directive_list(self: list):

        """Uses the map_flags dict from subclass to build a directives list."""
        # Add in dict logic from PR comment here.
        pass

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

    def write_job_card(self):
        raise NotImplementedError
