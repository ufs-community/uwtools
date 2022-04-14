"""
Slurm scheduler representation
"""
from src.uwtools.generic_scheduler import Scheduler

# __all__ = ["Slurm"]  # pylint


class Slurm(Scheduler):
    """Slurm scheduler representation"""

    def map_flags(self):
        raise NotImplementedError

    def add_native_flag(self, flag):
        raise NotImplementedError

    def create_directive_list(self):
        raise NotImplementedError
