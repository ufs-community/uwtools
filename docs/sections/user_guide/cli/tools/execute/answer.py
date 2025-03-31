from iotaa import asset, task

from uwtools.api.driver import AssetsTimeInvariant
from uwtools.api.logging import use_uwtools_logger

use_uwtools_logger()


class Answer(AssetsTimeInvariant):

    @task
    def answerfile(self):
        """
        A file containing the answer.
        """
        path = self.rundir / "answer.txt"
        yield self.taskname("Answer file")
        yield asset(path, path.is_file)
        yield None
        path.parent.mkdir(parents=True)
        with open(path, "w", encoding="utf-8") as f:
            print(self.config["n"], file=f)

    @classmethod
    def driver_name(cls):
        return "answer"
