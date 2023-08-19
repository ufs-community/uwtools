# pylint: disable=missing-function-docstring,protected-access,redefined-outer-name
"""
Tests for uwtools.utils.templater module.
"""

import os
from unittest.mock import patch

import yaml
from pytest import fixture, raises

from uwtools.logger import Logger
from uwtools.utils import templater


@fixture
def config_file(tmp_path):
    path = tmp_path / "config.yaml"
    yaml = """
roses: red
violets: blue
cannot:
    override: this
"""
    with open(path, "w", encoding="utf-8") as f:
        f.write(yaml)
    return str(path)


@fixture
def input_template(tmp_path):
    path = tmp_path / "template.jinja2"
    with open(path, "w", encoding="utf-8") as f:
        f.write("roses are {{roses}}, violets are {{violets}}")
    return str(path)


def render(config_file, input_template, **kwargs):
    templater.render(
        config_file=config_file,
        key_eq_val_pairs=[],
        input_template=input_template,
        log=Logger(),
        **kwargs,
    )


def test_render(config_file, input_template, tmp_path):
    outfile = str(tmp_path / "out.txt")
    render(config_file, input_template, outfile=outfile)
    with open(outfile, "r", encoding="utf-8") as f:
        assert f.read().strip() == "roses are red, violets are blue"


def test_render_dry_run(caplog, config_file, input_template):
    render(config_file, input_template, outfile="/dev/null", dry_run=True)
    logmsgs = (record.msg for record in caplog.records)
    assert "roses are red, violets are blue" in logmsgs


def test_render_values_missing(caplog, config_file, input_template):
    # Read in the config, remove the "roses" key, then re-write it.
    with open(config_file, "r", encoding="utf-8") as f:
        cfgobj = yaml.safe_load(f.read())
    del cfgobj["roses"]
    with open(config_file, "w", encoding="utf-8") as f:
        f.write(yaml.dump(cfgobj))
    with raises(ValueError):
        render(config_file, input_template, outfile="/dev/null")
    logmsgs = list(record.msg for record in caplog.records)
    assert "Template requires values that were not provided:" in logmsgs
    assert "roses" in logmsgs


def test_render_values_needed(caplog, config_file, input_template):
    render(config_file, input_template, outfile="/dev/null", values_needed=True)
    logmsgs = (record.msg for record in caplog.records)
    for var in ("roses", "violets"):
        assert var in logmsgs


def test__set_up_config_obj_env():
    expected = {"roses": "white", "violets": "blue"}
    with patch.dict(os.environ, expected):
        actual = templater._set_up_config_obj(config_file=None, key_eq_val_pairs=[], log=Logger())
    assert actual["roses"] == "white"
    assert actual["violets"] == "blue"


def test__set_up_config_obj_file(config_file):
    expected = {"roses": "white", "violets": "blue", "cannot": {"override": "this"}}
    actual = templater._set_up_config_obj(
        config_file=config_file, key_eq_val_pairs=["roses=white"], log=Logger()
    )
    assert actual == expected
