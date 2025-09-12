"""
A mixin class providing tasks that stage files.
"""

from iotaa import tasks

from uwtools.fs import Copier, Linker
from uwtools.strings import STR


class FileStager:
    """
    A base class for tasks that stage files.
    """

    @tasks
    def files_copied(self):
        """
        Files copied for run.
        """
        taskname, config, rundir = self.taskname, self.config, self.rundir  # type: ignore[attr-defined]
        yield taskname("files copied")
        yield [Copier(config=config.get("files_to_copy", {}), target_dir=rundir).go()]

    @tasks
    def files_hardlinked(self):
        """
        Files hardlinked for run.
        """
        taskname, config, rundir = self.taskname, self.config, self.rundir  # type: ignore[attr-defined]
        yield taskname("files hardlinked")
        yield [
            Linker(
                config=config.get("files_to_hardlink", {}),
                target_dir=rundir,
                hardlink=True,
                fallback=STR.copy,
            ).go()
        ]

    @tasks
    def files_linked(self):
        """
        Files linked for run.
        """
        taskname, config, rundir = self.taskname, self.config, self.rundir  # type: ignore[attr-defined]
        yield taskname("files linked")
        yield [Linker(config=config.get("files_to_link", {}), target_dir=rundir).go()]
