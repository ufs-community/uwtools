"""
Helpers to be used when working with files and directories
"""

import logging
import os
import shutil
from datetime import datetime


def handle_existing(run_directory, exist_act):
    """Given a run directory, and an action to do if
    directory exists, delete or rename directory."""

    logging.getLogger(__name__)

    # Try to delete existing run directory if option is delete
    try:
        if exist_act == "delete" and os.path.isdir(run_directory):
            shutil.rmtree(run_directory)
    except (RuntimeError, FileExistsError) as del_error:
        msg = f"Could not delete directory {run_directory}"
        logging.critical(msg)
        raise RuntimeError(msg) from del_error

    # Try to rename existing run directory if caller chooses rename
    try:
        if exist_act == "rename" and os.path.isdir(run_directory):
            now = datetime.now()
            save_dir = "%s%s" % (run_directory, now.strftime("_%Y%m%d_%H%M%S"))
            shutil.move(run_directory, save_dir)
    except (RuntimeError, FileExistsError) as rename_error:
        msg = f"Could not rename directory {run_directory}"
        logging.critical(msg)
        raise RuntimeError(msg) from rename_error


def compare_files(expected, actual):
    """Compare the content of two files.  Doing this over filecmp.cmp since
    we may not be able to handle end-of-file character differences with it.
    Prints the contents of two compared files to std out if they do not match."""

    with open(expected, "r", encoding="utf-8") as expected_file:
        expected_content = expected_file.read().rstrip("\n")
    with open(actual, "r", encoding="utf-8") as actual_file:
        actual_content = actual_file.read().rstrip("\n")

    if expected_content != actual_content:
        print("The expected file looks like:")
        print(expected_content)
        print("*" * 80)
        print("The rendered file looks like:")
        print(actual_content)
        return False
    return True
