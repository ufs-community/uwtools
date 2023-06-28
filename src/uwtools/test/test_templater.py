# pylint: disable=missing-function-docstring

"""
Tests for templater tool.
"""

import argparse
import os
from unittest.mock import patch

from pytest import raises

from uwtools.cli import templater
from uwtools.test.support import compare_files, fixture_path


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


def test_set_template_bad_config_suffix(tmp_path):
    """
    Test that a bad config filename suffix is rejected.
    """

    badfile = str(tmp_path / "foo.shx")  # .shx is a bad suffix
    with open(badfile, "w", encoding="utf-8"):
        pass  # create empty file
    with raises(ValueError):
        templater.main(["-i", fixture_path("nml.IN"), "-c", badfile, "-d"])


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


def test_set_template_dry_run(capsys):
    """
    Test dry-run output of ingest namelist tool.
    """

    infile = fixture_path("nml.IN")
    expected = f"""
Running with args:
----------------------------------------------------------------------
----------------------------------------------------------------------
        outfile: None
 input_template: {infile}
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
""".lstrip()

    with patch.dict(os.environ, {"fruit": "banana", "vegetable": "tomato", "how_many": "22"}):
        templater.main(["-i", infile, "--dry_run"])
        actual = capsys.readouterr().out
        for line in expected.split("\n"):
            assert line in actual


def test_set_template_listvalues(capsys):
    """
    Test "values needed" output of ingest namelist tool.
    """

    infile = fixture_path("nml.IN")
    expected = f"""
Running with args:
----------------------------------------------------------------------
----------------------------------------------------------------------
        outfile: None
 input_template: {infile}
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
""".lstrip()

    templater.main(["-i", infile, "--values_needed"])
    actual = capsys.readouterr().out
    for line in expected.split("\n"):
        assert line in actual


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


def test_set_template_yaml_config(tmp_path):
    """
    Test that providing a YAML file with necessary settings works to fill in
    the Jinja template. Test the writing mechanism, too.
    """

    outfile = str(tmp_path / "test_render_from_yaml.nml")

    # Patch environment to ensure that values are being taken from the config
    # file, not the environment.

    with patch.dict(os.environ, {"fruit": "candy", "vegetable": "cookies", "how_many": "all"}):
        templater.main(
            ["-i", fixture_path("nml.IN"), "-c", fixture_path("fruit_config.yaml"), "-o", outfile]
        )
    assert compare_files(fixture_path("simple2.nml"), outfile)


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
