# pylint: disable=missing-function-docstring

import logging
import re

from iotaa import asset, external
from pytest import fixture

from uwtools.logging import log


@fixture
def logged(caplog):
    log.setLevel(logging.DEBUG)

    def logged_(s: str, full: bool = False, multiline: bool = False, regex: bool = False):
        assert len([x for x in (full, multiline, regex) if x]) < 2
        if full:
            return "\n".join(caplog.messages).strip() == s.strip()
        if multiline:
            return s.strip() in "\n".join(caplog.messages).strip()
        s = s if regex else re.escape(s)
        return any(re.match(rf"^.*{s}.*$", message) for message in caplog.messages)

    return logged_


@fixture
def ready_task():
    @external
    def ready(*args, **kwargs):  # pylint: disable=unused-argument
        yield "ready"
        yield asset(None, lambda: True)

    return ready
