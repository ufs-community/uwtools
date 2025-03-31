# pylint: disable=missing-function-docstring

import re

from iotaa import asset, external
from pytest import fixture


@fixture
def logged(caplog):
    def logged_(s: str, clear: bool = False, escape: bool = False):
        s = re.escape(s) if escape else s
        found = any(re.match(rf"^.*{s}.*$", message) for message in caplog.messages)
        if clear:
            caplog.clear()
        return found

    return logged_


@fixture
def ready_task():
    @external
    def ready(*args, **kwargs):  # pylint: disable=unused-argument
        yield "ready"
        yield asset(None, lambda: True)

    return ready
