#!/usr/bin/env python3
'''test driver (not Unit Test) for Name List Prototype codes'''
import os
from collections import UserDict
from uwtools.J2Template import J2Template

uwtools_pwd = os.path.dirname(__file__)
template_file = os.path.join(uwtools_pwd,"fixtures/nml.IN")
config_file = os.path.join(uwtools_pwd,"fixtures/nml.yaml")

j2t_obj = J2Template(configure_path=config_file,template_path=template_file)
print(j2t_obj.configure_obj)
print(j2t_obj.configure_obj.fruit)
print( isinstance(j2t_obj.configure_obj, UserDict))
