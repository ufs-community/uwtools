# pylint: disable=missing-function-docstring

# NB: pytest implicitly imports files named conftest.py into test modules in the current directory
# and in subdirectories.

from iotaa import asset, external
from pytest import fixture


@fixture
def truetask():
    @external
    def true(*args, **kwargs):  # pylint: disable=unused-argument
        yield "true"
        yield asset(True, lambda: True)

    return true
