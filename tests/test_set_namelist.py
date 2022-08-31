#pylint: disable=unused-variable
'''
Tests set_namelist_ingest using dry-run
'''
import os
from pathlib import Path,PurePath
import subprocess
import tempfile
import filecmp

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
 output
'''
    os.environ['fruit'] = 'bananas'
    os.environ['vegetable'] = 'tomatos'
    os.environ['how_many'] = 'much'

    result = str(subprocess.check_output([exec_test,'-i',input_file,
                                          '-c',config_file,'-o output','--dry_run']),'utf-8')
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
    with tempfile.NamedTemporaryFile(suffix='_out', prefix='test_',dir='/tmp') as out_file:
        subprocess.check_output([exec_test,'-i',input_file,
                                           '-c',config_file,'-o',out_file.name])
    with open(output_file,'r',encoding='utf-8') as file:
        outfile_contents = file.read()
    assert outcome == outfile_contents

    out_file.close()

def test_set_namelest_functional():
    '''functional test for set_namelist'''
    input_nml_yaml = Path().joinpath(uwtools_pwd,'fixtures/input.nml.IN.yaml')
    input_nml_in   = Path().joinpath(uwtools_pwd,'fixtures/input.nml.IN')
    check_nml_output_file = Path().joinpath(uwtools_pwd,'fixtures/input.nml.f90')

    the_env = os.environ.copy()
    the_env['SKEB']='999'
    with tempfile.NamedTemporaryFile(suffix='.f90',prefix='input_nml',dir='/tmp') as output_nml_f90:
        subprocess.check_output([exec_test,'-i',input_nml_in,'-c',input_nml_yaml,
                                           '--set','SHUM=-99.0','SPPT=-979.0',
                                           '-o',output_nml_f90.name],env=the_env)

        assert filecmp.cmp( output_nml_f90.name, check_nml_output_file )
