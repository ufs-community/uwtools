# pylint: disable=missing-function-docstring
"""
Test fixtures for package uwtools.drivers.
"""

# NB: pytest implicitly imports files named conftest.py into test modules in the current directory
# and in subdirectories.

from iotaa import asset, external
from pytest import fixture


@fixture
def ready_task():
    @external
    def t():
        yield "ok"
        yield asset(None, lambda: True)

    return t
