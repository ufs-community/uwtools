from random import randint

from iotaa import asset, task

from uwtools.api.driver import AssetsTimeInvariant
from uwtools.api.logging import use_uwtools_logger

use_uwtools_logger()


class Rand(AssetsTimeInvariant):

    @task
    def randfile(self):
        """
        A file containing a random integer.
        """
        path = self.rundir / "randint"
        yield self.taskname("Random-integer file")
        yield asset(path, path.is_file)
        yield None
        path.parent.mkdir(parents=True)
        with open(path, "w", encoding="utf-8") as f:
            print(randint(self.config["lo"], self.config["hi"]), file=f)

    @property
    def driver_name(self):
        return "rand"
