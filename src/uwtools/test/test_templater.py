# pylint: disable=missing-function-docstring

"""
Tests for templater tool.
"""
import argparse
import io
import os
import tempfile
from contextlib import redirect_stdout
from unittest.mock import patch

import pytest
from pytest import raises

from uwtools.cli import templater
from uwtools.test.support import compare_files, fixture_path

uwtools_file_base = os.path.join(os.path.dirname(__file__))


@pytest.mark.skip()
def test_set_template_dryrun():
    """Unit test for checking dry-run output of ingest namelist tool"""

    input_file = os.path.join(uwtools_file_base, "fixtures/nml.IN")
    outcome = (
        """Running set_template with args:
----------------------------------------------------------------------
----------------------------------------------------------------------
        outfile: None
 input_template: """
        + input_file
        + """
    config_file: None
   config_items: []
        dry_run: True
  values_needed: False
        verbose: False
          quiet: False
----------------------------------------------------------------------
----------------------------------------------------------------------
&salad
  base = 'kale'
  fruit = 'banana'
  vegetable = 'tomato'
  how_many = 22
  dressing = 'balsamic'
/
"""
    )
    os.environ["fruit"] = "banana"
    os.environ["vegetable"] = "tomato"
    os.environ["how_many"] = "22"

    args = [
        "-i",
        input_file,
        "--dry_run",
    ]

    # Capture stdout for the dry run
    outstring = io.StringIO()
    with redirect_stdout(outstring):
        templater.main(args)
    result = outstring.getvalue()

    for outcome_line in outcome.split("\n"):
        assert outcome_line in result


@pytest.mark.skip()
def test_set_template_listvalues():
    """Unit test for checking values_needed output of ingest namelist tool"""

    input_file = os.path.join(uwtools_file_base, "fixtures/nml.IN")

    outcome = (
        """Running set_template with args:
----------------------------------------------------------------------
----------------------------------------------------------------------
        outfile: None
 input_template: """
        + input_file
        + """
    config_file: None
   config_items: []
        dry_run: False
  values_needed: True
        verbose: False
          quiet: False
----------------------------------------------------------------------
----------------------------------------------------------------------
Values needed for this template are:
fruit
how_many
vegetable
"""
    )

    args = [
        "-i",
        input_file,
        "--values_needed",
    ]

    # Capture stdout for values_needed output
    outstring = io.StringIO()
    with redirect_stdout(outstring):
        templater.main(args)
    result = outstring.getvalue()

    for outcome_line in outcome.split("\n"):
        assert outcome_line in result


@pytest.mark.skip()
def test_set_template_yaml_config():
    """Test that providing a YAML file with necessary settings works to fill in
    the Jinja template. Test the writing mechanism, too"""

    input_file = os.path.join(uwtools_file_base, "fixtures/nml.IN")
    config_file = os.path.join(uwtools_file_base, "fixtures/fruit_config.yaml")
    expected_file = os.path.join(uwtools_file_base, "fixtures/simple2.nml")

    # Also make sure that we're really pulling from the input file. Set
    # environment variables different from those in config_file
    os.environ["fruit"] = "candy"
    os.environ["vegetable"] = "cookies"
    os.environ["how_many"] = "all"

    # Make sure the output file matches the expected output
    with tempfile.TemporaryDirectory(dir=".") as tmp_dir:
        out_file = f"{tmp_dir}/test_render_from_yaml.nml"

        args = [
            "-i",
            input_file,
            "-c",
            config_file,
            "-o",
            out_file,
        ]

        templater.main(args)
        assert compare_files(expected_file, out_file)


def test_mutually_exclusive_args():
    """
    Test that mutually-exclusive -q/-d args are rejected.
    """

    infile = fixture_path("fruit_config.yaml")
    with raises(argparse.ArgumentError):
        templater.main(["-i", infile, "-q", "-d"])


def test_set_template_all_good():
    """
    Confirm success using namelist input and shell config.
    """

    templater.main(["-i", fixture_path("nml.IN"), "-c", fixture_path("fruit_config.sh"), "-d"])


def test_set_template_command_line_config(capsys):
    """
    Test behavior when values are provided on the command line.
    """

    infile = fixture_path("nml.IN")
    expected = f"""
Running with args:
----------------------------------------------------------------------
----------------------------------------------------------------------
        outfile: None
 input_template: {infile}
    config_file: None
   config_items: ['fruit=pear', 'vegetable=squash', 'how_many=22']
        dry_run: True
  values_needed: False
        verbose: False
          quiet: False
----------------------------------------------------------------------
----------------------------------------------------------------------
&salad
  base = 'kale'
  fruit = 'pear'
  vegetable = 'squash'
  how_many = 22
  dressing = 'balsamic'
/
""".lstrip()

    templater.main(["-i", infile, "--dry_run", "fruit=pear", "vegetable=squash", "how_many=22"])
    actual = capsys.readouterr().out
    for line in expected.split("\n"):
        assert line in actual


def test_set_template_bad_config_suffix(tmp_path):
    """
    Test that a bad config filename suffix is rejected.
    """

    badfile = str(tmp_path / "foo.shx")  # .shx is a bad suffix
    with open(badfile, "w", encoding="utf-8"):
        pass  # create empty file
    with raises(ValueError):
        templater.main(["-i", fixture_path("nml.IN"), "-c", badfile, "-d"])


def test_set_template_verbosity(capsys):
    infile = fixture_path("nml.IN")
    # #PM# WHAT TO DO ABOUT /dev/null BELOW?
    expected = f"""
Finished setting up debug file logging in /dev/null
Running with args:
----------------------------------------------------------------------
----------------------------------------------------------------------
        outfile: None
 input_template: {infile}
    config_file: None
   config_items: []
        dry_run: True
  values_needed: False
        verbose: True
          quiet: False
----------------------------------------------------------------------
----------------------------------------------------------------------
&salad
  base = 'kale'
  fruit = 'banana'
  vegetable = 'tomato'
  how_many = 22
  dressing = 'balsamic'
/
J2Template._load_file INPUT Args:
{infile}
""".lstrip()

    # Test verbose output when missing a required template value.

    env = {"fruit": "banana", "how_many": "22"}  # missing "vegetable"
    with patch.dict(os.environ, env):
        with raises(ValueError) as error:
            templater.main(["-i", infile, "--dry_run", "-v"])
        assert str(error.value) == "Missing values needed by template"

    # Test verbose output when all template values are available.

    env["vegetable"] = "tomato"
    with patch.dict(os.environ, env):
        templater.main(["-i", infile, "--dry_run", "-v"])
    actual = capsys.readouterr().out
    for line in expected.split("\n"):
        assert line in actual

    # Test quiet level.

    # PM# WHAT'S THE RATIONALE HERE?

    with raises(argparse.ArgumentError):
        templater.main(["-i", infile, "-q"])


def test_set_template_yaml_config_model_configure(tmp_path):
    """
    Test behavior when reading a simple model_configure file.
    """

    outfile = f"{tmp_path}/test_render_from_yaml.nml"
    args = [
        "-i",
        fixture_path("model_configure.sample.IN"),
        "-c",
        fixture_path("model_configure.values.yaml"),
        "-o",
        outfile,
    ]
    templater.main(args)
    assert compare_files(fixture_path("model_configure.sample"), outfile)
