'''
Set of test for Jinja2Config Class
'''
#pylint: disable=unused-variable
import os
from uwtools.J2Template import J2Template

uwtools_pwd = os.path.dirname(__file__)
template_file = os.path.join(uwtools_pwd,"fixtures/nml.IN")
config_file = os.path.join(uwtools_pwd,"fixtures/nml.yaml")

def test_jinja_config_class():
    '''tests the Jinja2 Config Class directly using yaml file in constructor'''

    jinja = J2Template(configure_path=config_file, template_path=template_file)
    render = jinja.render_template()

    outcome=\
"""&salad
  base = kale
  fruit = bananas
  vegetable = tomatos
  how_many = much
  dressing = balsamic
/"""

    assert render == outcome

def test_jinja_config_undeclared_variables():
    '''tests the Jinja2 Config Class directly using yaml file in constructor'''

    jinja = J2Template(configure_path=config_file, template_path=template_file)
    undeclared_variables = jinja.undeclared_variables()
    outcome={'fruit', 'how_many', 'vegetable'}
    assert undeclared_variables == outcome
