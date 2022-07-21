#pylint: disable=unused-variable
"""
Tests set_namelist_ingest using dry-run
"""
import os
import pathlib
import subprocess

def test_set_namelist_ingest_dryrun():
    """Unit test for checking dry-run output of ingest namelist tool"""

    outcome=\
"""&salad
    base = 'kale'
    fruit = 'banana'
    vegetable = 'tomato'
    how_many = 'much'
    dressing = 'balsamic'
/
"""
    os.environ['fruit'] = 'banana'
    os.environ['vegetable'] = 'tomato'
    os.environ['how_many'] = 'much'

    uwtools_pwd = os.path.join(os.path.dirname(__file__))
    exec_test= pathlib.Path(os.path.join(uwtools_pwd,"../src/uwtools/set_namelist_ingest.py"))
    input_file = pathlib.Path(os.path.join(uwtools_pwd,"fixtures/nml.IN"))

    result = str(subprocess.check_output([exec_test,'-i',input_file,'-d']),'utf-8')

    assert result == outcome

def test_set_namelist_ingest_listvalues():
    """Unit test for checking values_needed output of ingest namelist tool"""

    outcome=\
'''vegetable
fruit
how_many
'''
    os.environ['fruit'] = 'banana'
    os.environ['vegetable'] = 'tomato'
    os.environ['how_many'] = 'much'

    uwtools_pwd = os.path.join(os.path.dirname(__file__))
    exec_test= pathlib.Path(os.path.join(uwtools_pwd,"../src/uwtools/set_namelist_ingest.py"))
    input_file = pathlib.Path(os.path.join(uwtools_pwd,"fixtures/nml.IN"))

    result = str(subprocess.check_output([exec_test,'-i',input_file,'--values_needed']),'utf-8')
