'''
Set of test for Jinja2Config Class
'''
#pylint: disable=unused-variable
import os
from uwtools.jinja_config import Jinja2Config

uwtools_pwd = os.path.dirname(__file__)

def test_jinja_config_class():
    '''tests the Jinja2 Config Class directly using yaml file in constructor'''
    template_file = os.path.join(uwtools_pwd,"fixtures/nml.IN")
    config_file = os.path.join(uwtools_pwd,"fixtures/nml.yaml")

    jinja = Jinja2Config(template_file=template_file, config_file=config_file)
    render = jinja.template.render(jinja.yaml_config)

    outcome=\
"""&salad
  base = kale
  fruit = bananas
  vegetable = tomatos
  how_many = much
  dressing = balsamic
/"""
    assert render == outcome
