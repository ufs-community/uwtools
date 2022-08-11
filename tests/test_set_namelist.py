#pylint: disable=unused-variable
'''
Tests set_namelist_ingest using dry-run
'''
import os
from pathlib import Path,PurePath
import subprocess

uwtools_pwd = PurePath(__file__).parents[0]
exec_test = PurePath().joinpath(uwtools_pwd,'../src/uwtools/set_namelist.py')
input_file = PurePath().joinpath(uwtools_pwd,'fixtures/nml.IN')
config_file = PurePath().joinpath(uwtools_pwd,'fixtures/nml.yaml')
output_file = Path().joinpath(uwtools_pwd,'fixtures/nml.f90')

def test_set_namelist_ingest_dryrun():
    '''Unit test for checking dry-run output of ingest namelist tool'''

    outcome=\
'''&salad
    base = 'kale'
    fruit = 'bananas'
    vegetable = 'tomatos'
    how_many = 'much'
    dressing = 'balsamic'
/
'''
    os.environ['fruit'] = 'bananas'
    os.environ['vegetable'] = 'tomatos'
    os.environ['how_many'] = 'much'

    result = str(subprocess.check_output([exec_test,'-i',input_file,
                                          '-c',config_file,'--dry_run']),'utf-8')
    assert result == outcome

def test_set_namelist_ingest_listvalues():
    '''Unit test for checking values_needed output of ingest namelist tool'''

    outcome=['fruit','how_many','vegetable']
    result = str(subprocess.check_output([exec_test,'-i',input_file,
                                         '-c',config_file,'--values_needed']),'utf-8').splitlines()
    assert result.sort() == outcome.sort()

def test_set_namelist_ingest_outputfile():
    '''Unit test for checking dry-run output of ingest namelist tool'''

    outcome=\
'''&salad
    base = 'kale'
    fruit = 'bananas'
    vegetable = 'tomatos'
    how_many = 'much'
    dressing = 'balsamic'
/
'''
    Path.unlink(output_file,missing_ok=True)
    result = str(subprocess.check_output([exec_test,'-i',input_file,
                                         '-c',config_file,'-o',output_file]),'utf-8')
    with open(output_file,'r',encoding='utf-8') as file:
        outfile_contents = file.read()
    assert outcome == outfile_contents
    Path.unlink(output_file,missing_ok=True)
