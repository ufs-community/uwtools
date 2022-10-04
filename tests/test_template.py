'''
Unit tests for testing Template Class
'''
#pylint: disable=unused-variable
import os
from uwtools.template import TemplateConstants, Template
from uwtools.j2template import J2Template

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





def test_dump_file():
   # create a config dict
   test_config = {'greeting': 'Hello',
   		  'the_world': 'the world'
   		 }
   # final string we expect from dump file contents
   final = 'Hello to the world'
   
   # uses our J2Template and config dict get file contents 
   template = J2Template(test_config, template_str="{{greeting}} to {{the_world}}")
   # test template is equal to final str output
   assert template.render_template() == final


   # create a temp file to dump our contents
   with tempfile.TemporaryDirectory(dir='.') as tmp_dir:
   	out_file = f'{tmp_dir}/test_IN_dump.IN
   	test_config.dump_file(out_file)
   	
   	assert .....

   # other tests to confirm config was created correctly
   assert template.configure_obj.get('greeting') == 'Hello'    
   assert template.configure_obj.get('the_world') == 'the world'

def test_load_file():
   template_path = J2Template(template_path="/path/to/test/file")
   test_config = {
   	'greeting': 'Hello',
	'the_world': 'the world'
   }
   template = J2Template(test_config, template_str="{{greeting}} to {{the_world}}")
   assert J2Template.load_file(template_path) == template

def test_load_string():
   template_str = 'Hello to the world'
   dictonary = {
   	'greeting': 'Hello'
   	'the_world': 'the world'
   }
   template = ......
   assert J2Template.load_string(template_str) == template
