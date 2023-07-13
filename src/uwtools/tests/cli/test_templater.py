# pylint: disable=duplicate-code,missing-function-docstring
"""
Tests for the templater CLI.
"""

import argparse
import os
from pathlib import Path
from types import SimpleNamespace as ns
from unittest.mock import patch

import pytest
from pytest import raises

from uwtools.cli import templater
from uwtools.tests.support import compare_files, fixture_path, line_in_lines

# NB: Ensure that at least one test exercises both short and long forms of each
#     CLI switch.


@pytest.mark.parametrize(
    "sw", [ns(d="-d", i="-i", q="-q"), ns(d="--dry-run", i="--input-template", q="--quiet")]
)
def test_mutually_exclusive_args(sw):
    """
    Test that mutually-exclusive -q/-d args are rejected.
    """
    with raises(argparse.ArgumentError):
        argv = ["test", sw.i, fixture_path("fruit_config.yaml"), sw.d, sw.q]
        with patch.object(templater.sys, "argv", argv):
            templater.main()


@pytest.mark.parametrize(
    "sw", [ns(c="-c", d="-d", i="-i"), ns(c="--config-file", d="--dry-run", i="--input-template")]
)
def test_set_template_all_good(sw):
    """
    Confirm success using namelist input and shell config.
    """
    argv = ["test", sw.i, fixture_path("nml.IN"), sw.c, fixture_path("fruit_config.sh"), sw.d]
    with patch.object(templater.sys, "argv", argv):
        templater.main()


@pytest.mark.parametrize(
    "sw", [ns(c="-c", d="-d", i="-i"), ns(c="--config-file", d="--dry-run", i="--input-template")]
)
def test_set_template_bad_config_suffix(sw, tmp_path):
    """
    Test that a bad config filename suffix is rejected.
    """
    badfile = str(tmp_path / "foo.shx")  # .shx is a bad suffix
    Path(badfile).touch()
    with raises(ValueError):
        argv = ["test", sw.i, fixture_path("nml.IN"), sw.c, badfile, sw.d]
        with patch.object(templater.sys, "argv", argv):
            templater.main()


@pytest.mark.parametrize("sw", [ns(d="-d", i="-i"), ns(d="--dry-run", i="--input-template")])
def test_set_template_command_line_config(sw, capsys):
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
Re-run settings: {sw.i} {infile} {sw.d} fruit=pear vegetable=squash how_many=22
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
    argv = ["test", sw.i, infile, sw.d, "fruit=pear", "vegetable=squash", "how_many=22"]
    with patch.object(templater.sys, "argv", argv):
        templater.main()
    actual = capsys.readouterr().out.split("\n")
    for line in expected.split("\n"):
        assert line_in_lines(line, actual)


@pytest.mark.parametrize("sw", [ns(d="-d", i="-i"), ns(d="--dry-run", i="--input-template")])
def test_set_template_dry_run(sw, capsys):
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
Re-run settings: {sw.i} {infile} {sw.d}
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
        argv = ["test", sw.i, infile, sw.d]
        with patch.object(templater.sys, "argv", argv):
            templater.main()
        actual = capsys.readouterr().out.split("\n")
        for line in expected.split("\n"):
            assert line_in_lines(line, actual)


@pytest.mark.parametrize("sw", [ns(i="-i"), ns(i="--input-template")])
def test_set_template_listvalues(sw, capsys):
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
Re-run settings: {sw.i} {infile} --values-needed
----------------------------------------------------------------------
----------------------------------------------------------------------
Values needed for this template are:
fruit
how_many
vegetable
""".lstrip()
    argv = ["test", sw.i, infile, "--values-needed"]
    with patch.object(templater.sys, "argv", argv):
        templater.main()
    actual = capsys.readouterr().out.split("\n")
    for line in expected.split("\n"):
        assert line_in_lines(line, actual)


@pytest.mark.parametrize(
    "sw", [ns(d="-d", i="-i", v="-v"), ns(d="--dry-run", i="--input-template", v="--verbose")]
)
def test_set_template_verbosity(sw, capsys):
    infile = fixture_path("nml.IN")
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
Re-run settings: {sw.i} {infile} {sw.d} {sw.v}
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
            argv = ["test", sw.i, infile, sw.d, sw.v]
            with patch.object(templater.sys, "argv", argv):
                templater.main()
        assert str(error.value) == "Missing values needed by template"

    # Test verbose output when all template values are available.

    env["vegetable"] = "tomato"
    with patch.dict(os.environ, env):
        argv = ["test", "-i", infile, "--dry-run", "-v"]
        with patch.object(templater.sys, "argv", argv):
            templater.main()
    actual = capsys.readouterr().out.split("\n")
    for line in expected.split("\n"):
        assert line_in_lines(line, actual)

    # Test quiet level.

    # PM# WHAT'S THE RATIONALE HERE?

    with raises(argparse.ArgumentError):
        argv = ["test", "-i", infile, "-q"]
        with patch.object(templater.sys, "argv", argv):
            templater.main()


@pytest.mark.parametrize(
    "sw", [ns(c="-c", i="-i", o="-o"), ns(c="--config-file", i="--input-template", o="--outfile")]
)
def test_set_template_yaml_config(sw, tmp_path):
    """
    Test that providing a YAML file with necessary settings works to fill in the Jinja template.

    Test the writing mechanism, too.
    """
    outfile = str(tmp_path / "test_render_from_yaml.nml")

    # Patch environment to ensure that values are being taken from the config
    # file, not the environment.

    argv = [
        "test",
        sw.i,
        fixture_path("nml.IN"),
        sw.c,
        fixture_path("fruit_config.yaml"),
        sw.o,
        outfile,
    ]
    with patch.dict(os.environ, {"fruit": "candy", "vegetable": "cookies", "how_many": "all"}):
        with patch.object(templater.sys, "argv", argv):
            templater.main()
    assert compare_files(fixture_path("simple2.nml"), outfile)


@pytest.mark.parametrize(
    "sw", [ns(c="-c", i="-i", o="-o"), ns(c="--config-file", i="--input-template", o="--outfile")]
)
def test_set_template_yaml_config_model_configure(sw, tmp_path):
    """
    Test behavior when reading a simple model_configure file.
    """
    outfile = f"{tmp_path}/test_render_from_yaml.nml"
    argv = [
        "test",
        sw.i,
        fixture_path("model_configure.sample.IN"),
        sw.c,
        fixture_path("model_configure.values.yaml"),
        sw.o,
        outfile,
    ]
    with patch.object(templater.sys, "argv", argv):
        templater.main()
    assert compare_files(fixture_path("model_configure.sample"), outfile)
