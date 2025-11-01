import iotaa

from uwtools.drivers.driver import AssetsCycleBased


class TestDriver(AssetsCycleBased):
    """
    TestDriver.
    """

    @iotaa.task
    def forty_two(self):
        """
        Forty Two.
        """

    @classmethod
    def driver_name(cls): ...
