from random import randint

from iotaa import asset, task

from uwtools.api.driver import DriverCycleBased
from uwtools.api.logging import use_uwtools_logger

use_uwtools_logger()


class Rand(DriverCycleBased):
    """
    A random-number driver.
    """

    @task
    def randfile(self):
        """
        A file containing a random number.
        """
        path = self.rundir / "random"
        yield self.taskname("Random-number file")
        yield asset(path, path.is_file)
        yield None
        path.parent.mkdir(parents=True)
        with open(path, "w", encoding="utf-8") as f:
            print(randint(self.config["lo"], self.config["hi"]), file=f)

    @property
    def _driver_name(self):
        return "random"
