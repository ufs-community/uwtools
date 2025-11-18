"""
A mixin class providing tasks that stage files.
"""

from iotaa import collection

from uwtools.fs import Copier, Linker
from uwtools.strings import STR


class FileStager:
    """
    A base class for tasks that stage files.
    """

    @collection
    def files_copied(self):
        """
        Files copied for run.
        """
        taskname, config, rundir = self.taskname, self.config, self.rundir  # type: ignore[attr-defined]
        yield taskname("files copied")
        files = config.get("files_to_copy", {})
        yield Copier(config=files, target_dir=rundir).go() if files else None

    @collection
    def files_hardlinked(self):
        """
        Files hardlinked for run.
        """
        taskname, config, rundir = self.taskname, self.config, self.rundir  # type: ignore[attr-defined]
        yield taskname("files hardlinked")
        files = config.get("files_to_hardlink", {})
        yield (
            Linker(
                config=files,
                target_dir=rundir,
                hardlink=True,
                fallback=STR.copy,
            ).go()
            if files
            else None
        )

    @collection
    def files_linked(self):
        """
        Files linked for run.
        """
        taskname, config, rundir = self.taskname, self.config, self.rundir  # type: ignore[attr-defined]
        yield taskname("files linked")
        files = config.get("files_to_link", {})
        yield Linker(config=files, target_dir=rundir).go() if files else None
