from iotaa import asset, task

from uwtools.drivers.driver import AssetsCycleBased


class TestDriver(AssetsCycleBased):
    """
    TestDriver.
    """

    @task
    def forty_two(self):
        """
        42
        """
        yield "42"
        yield asset(42, lambda: True)
        yield None

    @classmethod
    def driver_name(cls):
        return "testdriver"
