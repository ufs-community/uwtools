# pylint: disable=missing-function-docstring,protected-access,redefined-outer-name
"""
Tests for uwtools.utils.templater module.
"""

import logging

import yaml
from pytest import fixture, raises

from uwtools.tests.support import logged
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
        **kwargs,
    )


def test_render(config_file, input_template, tmp_path):
    outfile = str(tmp_path / "out.txt")
    render(config_file, input_template, outfile=outfile)
    with open(outfile, "r", encoding="utf-8") as f:
        assert f.read().strip() == "roses are red, violets are blue"


def test_render_dry_run(caplog, config_file, input_template):

    logging.getLogger().setLevel(logging.DEBUG)
    render(config_file, input_template, outfile="/dev/null", dry_run=True)
    assert logged(caplog, "roses are red, violets are blue")


def test_render_values_missing(caplog, config_file, input_template):
    # Read in the config, remove the "roses" key, then re-write it.
    with open(config_file, "r", encoding="utf-8") as f:
        cfgobj = yaml.safe_load(f.read())
    del cfgobj["roses"]
    with open(config_file, "w", encoding="utf-8") as f:
        f.write(yaml.dump(cfgobj))
    with raises(ValueError):
        render(config_file, input_template, outfile="/dev/null")
    assert logged(caplog, "Template requires values that were not provided:")
    assert logged(caplog, "roses")


def test_render_values_needed(caplog, config_file, input_template):
    logging.getLogger().setLevel(logging.DEBUG)
    render(config_file, input_template, outfile="/dev/null", values_needed=True)
    for var in ("roses", "violets"):
        assert logged(caplog, var)


def test__set_up_config_obj(config_file):
    expected = {"roses": "white", "violets": "blue", "cannot": {"override": "this"}}
    actual = templater._set_up_config_obj(config_file=config_file, key_eq_val_pairs=["roses=white"])
    assert actual == expected
