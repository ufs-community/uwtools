# pylint: disable=missing-function-docstring

import logging
import re

from iotaa import asset, external
from pytest import fixture

from uwtools.logging import log


@fixture
def logged(caplog):
    log.setLevel(logging.DEBUG)

    def logged_(
        s: str,
        clear: bool = False,
        full: bool = False,
        multiline: bool = False,
        regex: bool = False,
    ):
        assert not (full and multiline)
        if full:
            found = "\n".join(caplog.messages).strip() == s.strip()
        elif multiline:
            found = s in "\n".join(caplog.messages)
        else:
            s = s if regex else re.escape(s)
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
