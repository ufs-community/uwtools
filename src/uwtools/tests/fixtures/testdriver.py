from iotaa import asset, task

from uwtools.drivers.driver import AssetsCycleBased


class TestDriver(AssetsCycleBased):
    """
    TestDriver.
    """

    @task
    def eighty_eight(self):
        """
        88
        """
        yield "88"
        yield asset(88, lambda: True)
        yield None

    @classmethod
    def driver_name(cls):
        return "testdriver"
