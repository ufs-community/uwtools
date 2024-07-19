from iotaa import asset, task

from uwtools.drivers.driver import AssetsTimeInvariant


class TestDriver(AssetsTimeInvariant):
    """
    Test Driver.
    """

    @task
    def eighty_eight(self):
        """
        Doc string.
        """
        yield "88"
        yield asset("88", lambda: True)
        yield None
    
    @property
    def _driver_name(self):
        return "testdriver"
