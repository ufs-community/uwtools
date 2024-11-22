# pylint: disable=missing-function-docstring
"""
Test fixtures for package uwtools.drivers.
"""

# NB: pytest implicitly imports files named conftest.py into test modules in the current directory
# and in subdirectories.

import iotaa
from pytest import fixture


@fixture
def ready_task():
    @iotaa.external
    def t():
        yield "ok"
        yield iotaa.asset(None, lambda: True)

    return t
