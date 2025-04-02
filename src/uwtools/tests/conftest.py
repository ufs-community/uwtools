import logging
import re
from datetime import datetime, timezone

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
    def ready(*_args, **_kwargs):
        yield "ready"
        yield asset(None, lambda: True)

    return ready


@fixture
def utc():
    def datetime_utc(*args, **kwargs) -> datetime:
        # See https://github.com/python/mypy/issues/6799
        tz = timezone.utc
        dt = datetime(*args, **kwargs, tzinfo=tz) if args or kwargs else datetime.now(tz=tz)  # type: ignore[misc]
        return dt.replace(tzinfo=None)

    return datetime_utc
