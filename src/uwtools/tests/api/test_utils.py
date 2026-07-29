from uwtools.api import utils
from uwtools.utils.file import atomic
from uwtools.utils.processing import run_shell_cmd


def test_api_utils_atomic():
    assert utils.atomic is atomic


def test_api_utils_run_shell_cmd():
    assert utils.run_shell_cmd is run_shell_cmd
