"""
Helpers for working with files and directories.
"""

import logging
import os
import shutil
from datetime import datetime as dt


def handle_existing(run_directory: str, exist_act: str) -> None:
    """
    Given a run directory, and an action to do if directory exists, delete or rename directory.
    """

    # Try to delete existing run directory if option is delete.

    try:
        if exist_act == "delete" and os.path.isdir(run_directory):
            shutil.rmtree(run_directory)
    except (FileExistsError, RuntimeError) as e:
        msg = f"Could not delete directory {run_directory}"
        logging.critical(msg)
        raise RuntimeError(msg) from e

    # Try to rename existing run directory if option is rename.

    try:
        if exist_act == "rename" and os.path.isdir(run_directory):
            now = dt.now()
            save_dir = "%s%s" % (run_directory, now.strftime("_%Y%m%d_%H%M%S"))
            shutil.move(run_directory, save_dir)
    except (FileExistsError, RuntimeError) as e:
        msg = f"Could not rename directory {run_directory}"
        logging.critical(msg)
        raise RuntimeError(msg) from e
