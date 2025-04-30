from unittest.mock import patch

from uwtools.api import logging as uw_logging


def test_use_uwtools_logger():
    kwargs = dict(quiet=False, verbose=True)
    with patch.object(uw_logging, "_setup_logging") as _setup_logging:
        uw_logging.use_uwtools_logger(**kwargs)
    _setup_logging.assert_called_once_with(**kwargs)
