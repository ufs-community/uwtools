"""
Encapsulates string based memory conversions
"""

import math


MAP = {"KB": 1000, "MB": 1000 * 1000, "GB": 1000 * 1000 * 1000}


class Memory:
    """represents memory as quantity and measurement

    100MB -> 100(quatity)MB(measurement)
    """

    def __init__(self, value):
        self._value = value
        self._measurement = None
        self._quantity = None

    def __str__(self):
        if float.is_integer(self.quantity):
            return str(self.quantity).replace(f".0", "") + self.measurement
        return str(self.quantity) + self.measurement

    @property
    def measurement(self):
        if self._measurement is None:
            self._measurement = self._value[-2:]
        return self._measurement

    @property
    def quantity(self):
        """returns the quantity"""
        if self._quantity is None:
            self._quantity = float(self._value[0:-2])
        return self._quantity

    def convert(self, measurement: str):
        """converts the current representation to another measurement"""
        quantity = (MAP[self.measurement] / MAP[measurement.upper()]) * self.quantity

        return Memory(str(quantity) + measurement.upper())


def round_up(n, decimals=0):
    multiplier = 10**decimals
    return math.ceil(n * multiplier) / multiplier


if __name__ == "__main__":
    pass
