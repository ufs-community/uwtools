# pylint: disable=missing-function-docstring

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
    """Test log file"""

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

    # Make sure log to file created messages
    try:
        with open(logfile, "r", encoding="utf-8") as fh:
            log_msgs = fh.readlines()
    except Exception as e:
        raise AssertionError(f"failed reading log file as {e}") from e

    # Ensure number of messages are same
    log_msgs_in_logfile = len(log_msgs)
    assert log_msgs_in_logfile == number_of_log_msgs

    # Ensure messages themselves are same
    for line in log_msgs:
        lev = line.split("-")[3].strip().lower()
        message = line.split(":")[-1].strip()
        assert reference[lev] == message
