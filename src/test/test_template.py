"""
Unit tests for testing Template Class
"""
# pylint: disable=unused-variable
import os
import pathlib

from uwtools.j2template import J2Template

uwtools_file_base = os.path.join(os.path.dirname(__file__))

# Unit tests for testing J2Template Class


def test_dump_file():
    """
    Render template from input string provided.
    Check undeclared_variables returns expected list
    """
    template_str = "Hello to the world"
    output = {"greeting", "the_world"}
    test_config = {"greeting": "Hello", "the_world": "the world"}
    template = J2Template(test_config, template_str="{{greeting}} to {{the_world}}")
    assert template.configure_obj.get("greeting") == "Hello"
    assert template.configure_obj.get("the_world") == "the world"
    assert template.render_template() == template_str
    assert template.undeclared_variables == output


def test_load_file():
    """
    Load the Jinja2 template from the file provided.
    Returns
    -------
    Jinja2 Template object
    """
    template_str = "Hello to the world"
    output = {"greeting", "the_world"}
    test_config = {"greeting": "Hello", "the_world": "the world"}
    test_path = os.path.join(uwtools_file_base, pathlib.Path("fixtures/J2Template.IN"))
    template = J2Template(test_config, template_path=test_path)
    assert template.render_template() == template_str
    assert template.undeclared_variables == output


def test_load_string():
    """
    Load the Jinja2 template from the string provided.
    Returns
    -------
    Jinja2 Template object
    """
    template_str = "Hello to the world"
    test_config = {"greeting": "Hello", "the_world": "the world"}
    template = J2Template(test_config, template_str="{{greeting}} to {{the_world}}")
    assert template.render_template() == template_str
