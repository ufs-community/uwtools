import re
from copy import deepcopy
from importlib import resources
from pathlib import Path
from typing import Any, Callable, Union

import yaml
from _pytest.logging import LogCaptureFixture

from uwtools.config.validator import _validation_errors
from uwtools.utils.file import resource_path


def compare_files(path1: Union[Path, str], path2: Union[Path, str]) -> bool:
    """
    Determines whether the two given files are identical up to any number of trailing newlines,
    which are ignored. Print the contents of both files when they do not match.

    :param path1: Path to first file.
    :param path2: Path to second file.
    :return: Do the files match?
    """
    with open(path1, "r", encoding="utf-8") as f:
        content1 = f.read().rstrip("\n")
    with open(path2, "r", encoding="utf-8") as f:
        content2 = f.read().rstrip("\n")
    if content1 != content2:
        print("1st file looks like:")
        print(content1)
        print("*" * 80)
        print("2nd file looks like:")
        print(content2)
        return False
    return True


def fixture_pathobj(suffix: str = "") -> Path:
    """
    Return a pathlib Path object to a test-fixture resource file.

    :param suffix: A subpath relative to the location of the unit-test fixture resource files. The
        prefix path to the resources files is known to Python and varies based on installation
        location.
    """
    with resources.as_file(resources.files("uwtools.tests.fixtures")) as prefix:
        path = prefix / suffix
    return path


def fixture_path(suffix: str = "") -> Path:
    """
    Return a POSIX path to a test-fixture resource file.

    :param suffix: A subpath relative to the location of the unit-test fixture resource files. The
        prefix path to the resources files is known to Python and varies based on installation
        location.
    """
    return fixture_pathobj(suffix)


def logged(caplog: LogCaptureFixture, msg: str) -> bool:
    """
    Does the given message occur in the log capture?

    :param caplog: The pytest log capture.
    :param msg: The message sought.
    :return: Does it?
    """
    return msg in [record.message for record in caplog.records]


def regex_logged(caplog: LogCaptureFixture, msg: str) -> bool:
    """
    Does the given regex match a line in the log capture?

    :param caplog: The pytest log capture.
    :param msg: The regex sought.
    :return: Does it?
    """
    pattern = re.compile(re.escape(msg))
    return any(pattern.search(record.message) for record in caplog.records)


def schema_validator(schema_name: str, *args: Any) -> Callable:
    """
    Create a lambda that returns errors from validating a config input.

    :param schema_name: The uwtools schema name.
    :param args: Keys leading to sub-schema to be used to validate eventual input.
    :returns: A lambda that, when called with an input to test, returns a string (possibly empty)
        containing the validation errors.
    """
    with open(
        resource_path("jsonschema") / f"{schema_name}.jsonschema", "r", encoding="utf-8"
    ) as f:
        schema = yaml.safe_load(f)
    defs = schema.get("$defs", {})
    for arg in args:
        schema = schema[arg]
    schema.update({"$defs": defs})
    return lambda config: "\n".join(str(x) for x in _validation_errors(config, schema))


def with_del(d: dict, *args: Any) -> dict:
    """
    Delete a value at a given chain of keys in a dict.

    :param d: The dict to update.
    :param args: One or more keys navigating to the value to delete.
    """
    new = deepcopy(d)
    p = new
    for key in args[:-1]:
        p = p[key]
    del p[args[-1]]
    return new


def with_set(d: dict, val: Any, *args: Any) -> dict:
    """
    Set a value at a given chain of keys in a dict.

    :param d: The dict to update.
    :param val: The value to set.
    :param args: One or more keys navigating to the value to set.
    """
    new = deepcopy(d)
    p = new
    for key in args[:-1]:
        p = p[key]
    p[args[-1]] = val
    return new
