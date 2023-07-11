# pylint: disable=missing-function-docstring,protected-access
"""
Tests for uwtools.logging module.
"""

import logging

from pytest import raises

from uwtools.logger import Logger

level = "debug"
number_of_log_msgs = 5
reference = {
    "debug": "Logging test has started",
    "info": "Logging to 'logger.log' in the script dir",
    "warning": "This is my last warning, take heed",
    "error": "This is an error",
    "critical": "He's dead, She's dead.  They are all dead!",
}


def test_logger(tmp_path):
    """
    Test log file.
    """

    logfile = tmp_path / "logger.log"

    try:
        log = Logger("test_logger", level=level, log_file=logfile, colored_log=True)
        log.debug(reference["debug"])
        log.info(reference["info"])
        log.warning(reference["warning"])
        log.error(reference["error"])
        log.critical(reference["critical"])
    except Exception as e:
        raise AssertionError(f"logging failed as {e}") from e

    # Make sure log to file created messages:

    try:
        with open(logfile, "r", encoding="utf-8") as fh:
            log_msgs = fh.readlines()
    except Exception as e:
        raise AssertionError(f"failed reading log file as {e}") from e

    # Ensure number of messages are same:
    log_msgs_in_logfile = len(log_msgs)
    assert log_msgs_in_logfile == number_of_log_msgs

    # Ensure messages themselves are same:

    for line in log_msgs:
        lev = line.split("-")[3].strip().lower()
        message = line.split(":")[-1].strip()
        assert reference[lev] == message


def test_Logger_add_handlers(tmp_path):
    logfile = tmp_path / "log"
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    Logger.add_handlers(logger=logger, handlers=[logging.FileHandler(filename=logfile)])
    msg = "Hello!"
    logger.info(msg)
    with open(logfile, "r", encoding="utf-8") as f:
        assert msg in f.read()


def test_Logger_constructor_bad_level():
    with raises(LookupError):
        Logger(level="INVALID")


def test_Logger_get_file_handler(tmp_path):
    logdir = tmp_path / "subdir"
    logfile = logdir / "log"
    assert not logdir.is_dir()
    assert isinstance(Logger.get_file_handler(logfile_path=logfile), logging.Handler)
    assert logdir.is_dir()


def test_Logger_get_logger():
    logger = Logger()
    assert logger.get_logger() == logger._logger
