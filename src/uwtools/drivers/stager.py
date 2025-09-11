"""
A mixin class providing tasks that stage files.
"""

from iotaa import tasks

from uwtools.fs import Copier, Linker
from uwtools.strings import STR


# mypy: disable-error-code="attr-defined"
class FileStager:
    """
    A base class for tasks that stage files.
    """

    @tasks
    def files_copied(self):
        """
        Files copied for run.
        """
        yield self.taskname("files copied")
        yield [
            Copier(
                config=self.config.get("files_to_copy", {}),
                target_dir=self.rundir,
            ).go()
        ]

    @tasks
    def files_hardlinked(self):
        """
        Files hardlinked for run.
        """
        yield self.taskname("files hardlinked")
        yield [
            Linker(
                config=self.config.get("files_to_hardlink", {}),
                target_dir=self.rundir,
                hardlink=True,
                fallback=STR.copy,
            ).go()
        ]

    @tasks
    def files_linked(self):
        """
        Files linked for run.
        """
        yield self.taskname("files linked")
        yield [
            Linker(
                config=self.config.get("files_to_link", {}),
                target_dir=self.rundir,
            ).go()
        ]
