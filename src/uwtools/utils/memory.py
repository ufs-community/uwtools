"""
Encapsulates string based memory conversions.
"""


MAP = {"KB": 1000, "MB": 1000 * 1000, "GB": 1000 * 1000 * 1000}


class Memory:
    """
    Represents memory as quantity and measurement.

    100MB -> 100(quatity)MB(measurement)
    """

    def __init__(self, value):
        self._value = value
        self._measurement = None
        self._quantity = None

    def __str__(self):
        if float.is_integer(self.quantity):
            return str(self.quantity).replace(".0", "") + self.measurement
        return str(self.quantity) + self.measurement

    @property
    def measurement(self):
        """
        Returns the measurement (MB, KB, etc.)
        """
        if self._measurement is None:
            self._measurement = self._value[-2:]
        return self._measurement

    @property
    def quantity(self):
        """
        Returns the quantity.
        """
        if self._quantity is None:
            self._quantity = float(self._value[0:-2])
        return self._quantity

    def convert(self, measurement: str):
        """
        Converts the current representation to another measurement.
        """
        quantity = (MAP[self.measurement] / MAP[measurement.upper()]) * self.quantity

        return Memory(str(quantity) + measurement.upper())
