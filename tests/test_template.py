'''
Unit tests for testing Template Class
'''
#pylint: disable=unused-variable
import os
import pathlib
from uwtools.template import TemplateConstants, Template
from uwtools.j2template import J2Template

uwtools_file_base = os.path.join(os.path.dirname(__file__))

def test_substitute_string_from_dict():
    """
        Substitute with ${v}
    """
    template = '${greeting} to ${the_world}'
    dictionary = {
        'greeting': 'Hello',
        'the_world': 'the world'
    }
    final = 'Hello to the world'
    assert Template.substitute_structure(template,
           TemplateConstants.DOLLAR_CURLY_BRACE, dictionary.get) == final

def test_substitute_string_from_dict_paren():
    """
       Substitute with $(v)
    """
    template = '$(greeting) to $(the_world)'
    dictionary = {
        'greeting': 'Hello',
        'the_world': 'the world'
    }
    final = 'Hello to the world'
    assert Template.substitute_structure(template,
           TemplateConstants.DOLLAR_PARENTHESES, dictionary.get) == final


def test_assign_string_from_dict_paren():
    """
          Substitute with $(v) should replace with the actual object
    """
    template = '$(greeting)'
    dictionary = {
        'greeting': {
            'a': 1,
            'b': 2
        }
    }
    assert Template.substitute_structure(template,
                                         TemplateConstants.DOLLAR_PARENTHESES,
                                         dictionary.get) == dictionary['greeting']


def test_substitute_string_from_dict_double_curly():
    """
       Substitute with {{v}}
    """
    template = '{{greeting}} to {{the_world}}'
    dictionary = {
        'greeting': 'Hello',
        'the_world': 'the world'
    }
    final = 'Hello to the world'
    assert Template.substitute_structure(template,
                                         TemplateConstants.DOUBLE_CURLY_BRACES,
                                         dictionary.get) == final


def test_substitute_string_from_dict_at_square():
    """
        Substitute with @[v]
    """
    template = '@[greeting] to @[the_world]'
    dictionary = {
        'greeting': 'Hello',
        'the_world': 'the world'
    }
    final = 'Hello to the world'
    assert Template.substitute_structure(template,
                                         TemplateConstants.AT_SQUARE_BRACES,
                                         dictionary.get) == final


def test_substitute_string_from_dict_at_anglebrackets():
    """
        Substitute with @<v>
    """
    template = '@<greeting> to @<the_world>'
    dictionary = {
        'greeting': 'Hello',
        'the_world': 'the world'
    }
    final = 'Hello to the world'
    assert Template.substitute_structure(template,
                                         TemplateConstants.AT_ANGLE_BRACKETS,
                                         dictionary.get) == final


def test_substitute_string_from_environment():
    """
        Substitute from environment
    """
    template = '${GREETING} to ${THE_WORLD}'
    os.environ['GREETING'] = 'Hello'
    os.environ['THE_WORLD'] = 'the world'
    final = 'Hello to the world'
    assert Template.substitute_structure_from_environment(template) == final


def test_substitute_with_dependencies():
    """
         Substitute from environment with dependencies
    """
    inputs = {
        'root': '/home/user',
        'config_file': 'config.yaml',
        'config': '$(root)/config/$(config_file)',
        'greeting': 'hello $(world)',
        'world': 'world',
        'complex': '$(dictionary)',
        'dictionary': {
            'a': 1,
            'b': 2
        },
        'dd': { '2': 'a', '1': 'b' },
        'ee': { '3': 'a', '1': 'b' },
        'ff': { '4': 'a', '1': 'b $(greeting)' },
        'host': {
            'name': 'xenon',
            'config': '$(root)/hosts',
            'config_file': '$(config)/$(name).config.yaml',
            'proxy2': {
                'config': '$(root)/$(name).$(greeting).yaml',
                'list': [['$(root)/$(name)', 'toto.$(name).$(greeting)'], '$(config_file)']
            }
        }
    }
    output = {'complex': {'a': 1, 'b': 2},
                 'config': '/home/user/config/config.yaml',
                 'config_file': 'config.yaml',
                 'dd': {'1': 'b', '2': 'a'},
                 'dictionary': {'a': 1, 'b': 2},
                 'ee': {'1': 'b', '3': 'a'},
                 'ff': {'1': 'b hello world', '4': 'a'},
                 'greeting': 'hello world',
                 'host': {'config': '/home/user/hosts',
                          'config_file': '/home/user/config/config.yaml/xenon.config.yaml',
                          'name': 'xenon',
                          'proxy2': {'config': '/home/user/xenon.hello world.yaml',
                                     'list': [['/home/user/xenon', 'toto.xenon.hello world'],
                                              'config.yaml']}},
                 'root': '/home/user',
                 'world': 'world'}

    assert Template.substitute_with_dependencies(inputs,inputs,TemplateConstants.DOLLAR_PARENTHESES)==output




"""
Unit tests for testing J2Template Class
"""


def test_dump_file():
    """
         Write rendered template to the output_path provided
         Parameters
         ----------
         output_path : Path
    """
    test_config = {'greeting': 'Hello',
    		  'the_world': 'the world'
    }
    final = 'Hello to the world'
    template = J2Template(test_config, template_str="{{greeting}} to {{the_world}}")
    assert template.configure_obj.get('greeting') == 'Hello'
    assert template.configure_obj.get('the_world') == 'the world'
    assert template.render_template() == final
    """ 
    test_undeclared = template.undeclared_variables
    assert ['greeting'] in test_undeclared()
    """
    assert template.undeclared_variables == ['greeting']

def test_load_file():
    """
         Load the Jinja2 template from the file provided.
         Returns
         -------
         Jinja2 Template object
    """
    test_config = {
    	'greeting': 'Hello',
 	'the_world': 'the world'
    }
    template_str = 'Hello to the world'
    test_path = os.path.join(uwtools_file_base,pathlib.Path("fixtures/J2Template.IN"))
    template = J2Template(test_config, template_path=test_path)
    assert template.render_template() == template_str

def test_load_string():
    """
         Load the Jinja2 template from the string provided.
         Returns
         -------
         Jinja2 Template object
    """
    template_str = 'Hello to the world'
    test_config  = {
    	'greeting': 'Hello',
    	'the_world': 'the world'
    }
    template = J2Template(test_config, template_str="{{greeting}} to {{the_world}}")
    assert template.render_template() == template_str
