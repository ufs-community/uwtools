# pylint: disable=missing-function-docstring

from iotaa import asset, external
from pytest import fixture


@fixture
def ready_task():
    @external
    def ready(*args, **kwargs):  # pylint: disable=unused-argument
        yield "ready"
        yield asset(None, lambda: True)

    return ready
