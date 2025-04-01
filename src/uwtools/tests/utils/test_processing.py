# pylint: disable=missing-function-docstring
"""
Tests for uwtools.utils.processing module.
"""


from uwtools.utils import processing


def test_utils_processing_run_shell_cmd__failure(logged):
    cmd = "expr 1 / 0"
    success, output = processing.run_shell_cmd(cmd=cmd)
    assert "division by zero" in output
    assert success is False
    assert logged("Running: %s" % cmd)
    assert logged("Failed with status: 2")
    assert logged("Output:")
    assert logged("  expr: division by zero")


def test_utils_processing_run_shell_cmd__success(logged, tmp_path):
    cmd = "echo hello $FOO"
    success, _ = processing.run_shell_cmd(
        cmd=cmd, cwd=tmp_path, env={"FOO": "bar"}, log_output=True
    )
    assert success
    assert logged(f"Running: {cmd} in {tmp_path} with environment variables FOO=bar")
    assert logged("Output:")
    assert logged("  hello bar")
