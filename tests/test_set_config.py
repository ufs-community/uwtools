'''
Tests for set_config tool
'''

import argparse
import pathlib
import os
import tempfile
import io
from contextlib import redirect_stdout
import pytest
from uwtools import config
from uwtools import set_config

from uwtools.utils import cli_helpers


uwtools_file_base = os.path.join(os.path.dirname(__file__))

def compare_files(expected, actual):
    '''Compare the content of two files.  Doing this over filecmp.cmp since 
    we may not be able to handle end-of-file character differences with it.
    Prints the contents of two compared files to std out if they do not match.'''

    with open(expected, 'r', encoding='utf-8') as expected_file:
        expected_content = expected_file.read().rstrip('\n')
    with open(actual, 'r', encoding='utf-8') as actual_file:
        actual_content = actual_file.read().rstrip('\n')

    if expected_content != actual_content:
        print('The expected file looks like:')
        print(expected_content)
        print('*' * 80)
        print('The rendered file looks like:')
        print(actual_content)
        return False
    return True

def test_path_if_file_exists(): #pylint: disable=unused-variable
    '''Make sure the function works as expected.  It is used as a type in 
    argparse, so raises an argparse exception when the user provides a 
    non-existant path.'''

    with tempfile.NamedTemporaryFile(dir='.', mode='w') as tmp_file:
        assert cli_helpers.path_if_file_exists(tmp_file.name)

    with pytest.raises(argparse.ArgumentTypeError):
        not_a_filepath = './no_way_this_file_exists.nope'
        cli_helpers.path_if_file_exists(not_a_filepath)

def test_set_config_yaml_simple(): #pylint: disable=unused-variable
    ''' Test that providing a YAML base file with necessary settings 
    will create a YAML config file'''

    input_file = os.path.join(uwtools_file_base, pathlib.Path("fixtures/simple2.yaml"))

    with tempfile.TemporaryDirectory(dir='.') as tmp_dir:

        out_file = f'{tmp_dir}/test_config_from_yaml.yaml'
        args = ['-i', input_file, '-o', out_file]

        set_config.create_config_obj(args)

        expected = config.YAMLConfig(input_file)
        expected_file = f'{tmp_dir}/expected_yaml.yaml'
        expected.dump_file(expected_file)

        assert compare_files(expected_file, out_file)

def test_set_config_ini_simple(): #pylint: disable=unused-variable
    ''' Test that providing a basic INI file with necessary settings 
    will create an INI config file'''

    input_file = os.path.join(uwtools_file_base, pathlib.Path("fixtures/simple.ini"))

    with tempfile.TemporaryDirectory(dir='.') as tmp_dr:
        out_file = f'{tmp_dr}/test_config_from_ini.ini'
        args = ['-i', input_file, '-o', out_file]

        set_config.create_config_obj(args)

        expected = config.INIConfig(input_file)
        expected_file = f'{tmp_dr}/expected_ini.ini'
        expected.dump_file(expected_file)

        assert compare_files(expected_file, out_file)

def test_set_config_f90nml_simple(): #pylint: disable=unused-variable
    '''Test that providing basic f90nml file with necessary settings
    will create f90nml config file'''

    input_file = os.path.join(uwtools_file_base, pathlib.Path("fixtures/simple.nml"))

    with tempfile.TemporaryDirectory(dir='.') as tmp_dr:

        out_file = f'{tmp_dr}/test_config_from_nml.nml'
        args = ['-i', input_file, '-o', out_file]

        set_config.create_config_obj(args)

        expected = config.F90Config(input_file)
        expected_file = f'{tmp_dr}/expected_nml.nml'
        expected.dump_file(expected_file)

        assert compare_files(expected_file, out_file)

def test_set_config_bash_simple(): #pylint: disable=unused-variable
    '''Test that providing bash file with necessary settings will 
    create an INI config file'''

    input_file = os.path.join(uwtools_file_base, pathlib.Path("fixtures/simple.sh"))

    with tempfile.TemporaryDirectory(dir='.') as tmp_dr:

        out_file = f'{tmp_dr}/test_config_from_bash.ini'

        args = ['-i', input_file, '-o', out_file]

        set_config.create_config_obj(args)

        expected = config.INIConfig(input_file)
        expected_file = f'{tmp_dr}/expected_ini.ini'
        expected.dump_file(expected_file)

        assert compare_files(expected_file, out_file)

def test_set_config_yaml_config_file(): #pylint: disable=unused-variable
    '''Test that providing a yaml base input file and a config file will
    create and update yaml config file'''

    input_file = os.path.join(uwtools_file_base, pathlib.Path("fixtures/fruit_config.yaml"))
    config_file = os.path.join(uwtools_file_base, pathlib.Path("fixtures/fruit_config_similar.yaml"))

    with tempfile.TemporaryDirectory(dir='.') as tmp_dir:

        out_file = f'{tmp_dir}/test_config_from_yaml.yaml'
        args = ['-i', input_file, '-o', out_file, '-c', config_file]

        set_config.create_config_obj(args)

        expected = config.YAMLConfig(input_file)
        config_file_obj = config.YAMLConfig(config_file)
        expected.update_values(config_file_obj)
        expected_file = f'{tmp_dir}/expected_yaml.yaml'
        expected.dump_file(expected_file)

        assert compare_files(expected_file, out_file)

def test_set_config_f90nml_config_file(): #pylint: disable=unused-variable
    '''Test that providing a F90nml base input file and a config file will
    create and update F90nml config file'''

    input_file = os.path.join(uwtools_file_base, pathlib.Path("fixtures/simple.nml"))
    config_file = os.path.join(uwtools_file_base, pathlib.Path("fixtures/simple2.nml"))

    with tempfile.TemporaryDirectory(dir='.') as tmp_dir:

        out_file = f'{tmp_dir}/test_config_from_nml.nml'
        args = ['-i', input_file, '-o', out_file, '-c', config_file]

        set_config.create_config_obj(args)

        expected = config.F90Config(input_file)
        config_file_obj = config.F90Config(config_file)
        expected.update_values(config_file_obj)
        expected_file = f'{tmp_dir}/expected_nml.nml'
        expected.dump_file(expected_file)

        assert compare_files(expected_file, out_file)

def test_set_config_ini_config_file(): #pylint: disable=unused-variable
    '''Test that aproviding INI base input file and a config file will 
    create and update INI config file'''

    input_file = os.path.join(uwtools_file_base, pathlib.Path("fixtures/simple.ini"))
    config_file = os.path.join(uwtools_file_base, pathlib.Path("fixtures/simple2.ini"))

    with tempfile.TemporaryDirectory(dir='.') as tmp_dir:

        out_file = f'{tmp_dir}/test_config_from_ini.ini'
        args = ['-i', input_file, '-o', out_file, '-c', config_file]

        set_config.create_config_obj(args)

        expected = config.INIConfig(input_file)
        config_file_obj = config.INIConfig(config_file)
        expected.update_values(config_file_obj)
        expected_file = f'{tmp_dir}/expected_ini.ini'
        expected.dump_file(expected_file)

        assert compare_files(expected_file, out_file)

def test_set_config_ini_bash_config_file(): #pylint: disable=unused-variable
    '''Test that aproviding INI base input file and a config file will 
    create and update INI config file'''

    input_file = os.path.join(uwtools_file_base, pathlib.Path("fixtures/simple.ini"))
    config_file = os.path.join(uwtools_file_base, pathlib.Path("fixtures/fruit_config.sh"))

    with tempfile.TemporaryDirectory(dir='.') as tmp_dir:

        out_file = f'{tmp_dir}/test_config_from_ini.ini'
        args = ['-i', input_file, '-o', out_file, '-c', config_file]

        set_config.create_config_obj(args)

        expected = config.INIConfig(input_file)
        config_file_obj = config.INIConfig(config_file)
        expected.update_values(config_file_obj)
        expected_file = f'{tmp_dir}/expected_ini.ini'
        expected.dump_file(expected_file)

        assert compare_files(expected_file, out_file)

def test_incompatible_file_type(): #pylint: disable=unused-variable
    '''Test that providing an incompatible file type for input base file will 
    return print statement'''

    input_file = os.path.join(uwtools_file_base, pathlib.Path("fixtures/model_configure.sample"))
    args = ['-i', input_file]

    with pytest.raises(ValueError):
        set_config.create_config_obj(args)

def test_set_config_field_table(): #pylint: disable=unused-variable
    '''Test reading a YAML config object and generating a field file table.
    '''
    input_file = os.path.join(uwtools_file_base,pathlib.Path("fixtures","FV3_GFS_v16.yaml"))
    expected_file = os.path.join(uwtools_file_base,pathlib.Path("fixtures","field_table.FV3_GFS_v16"))

    with tempfile.TemporaryDirectory(dir='.') as tmp_dir:
        out_file = f'{tmp_dir}/field_table_from_yaml.FV3_GFS'
        args = ['-i', input_file, '-o', out_file, '--output_file_type', "FieldTable"]

        set_config.create_config_obj(args)

        with open(expected_file, 'r', encoding="utf-8") as file_1, open(out_file, 'r', encoding="utf-8") as file_2:
            reflist = [line.rstrip('\n').strip().replace("'", "") for line in file_1]
            outlist = [line.rstrip('\n').strip().replace("'", "") for line in file_2]
            lines = zip(outlist, reflist)
            for line1, line2 in lines:
                assert line1 in line2

def test_set_config_dry_run(): #pylint: disable=unused-variable
    ''' Test that providing a YAML base file with a dry run flag 
    will print an YAML config file'''

    input_file = os.path.join(uwtools_file_base, pathlib.Path("fixtures/fruit_config.yaml"))

    args = ['-i', input_file, '-d']

    expected = config.YAMLConfig(input_file)
    expected.dereference_all()
    expected_content = str(expected)

    outstring = io.StringIO()
    with redirect_stdout(outstring):
        set_config.create_config_obj(args)
    result = outstring.getvalue()

    assert result.rstrip('\n') == expected_content.rstrip('\n')


def test_show_format(): #pylint: disable=unused-variable
    '''Test providing required configuration format for a given input and target.
    '''
    input_file = os.path.join(uwtools_file_base,pathlib.Path("fixtures","FV3_GFS_v16.yaml"))
    outcome=\
    """Help on method dump_file in module uwtools.config:

dump_file(output_path) method of uwtools.config.FieldTableConfig instance
    Write the formatted output to a text file. 
    FMS field and tracer managers must be registered in an ASCII table called 'field_table'
    This table lists field type, target model and methods the querying model will ask for.
    
    See UFS documentation for more information:
    https://ufs-weather-model.readthedocs.io/en/ufs-v1.0.0/InputsOutputs.html#field-table-file
    
    The example format for generating a field file is::
    
    sphum:
      longname: specific humidity
      units: kg/kg
      profile_type: 
        name: fixed
        surface_value: 1.e30

None
"""

    with tempfile.TemporaryDirectory(dir='.') as tmp_dir:
        out_file = f'{tmp_dir}/field_table_from_yaml.FV3_GFS'
        args = ['-i', input_file, '-o', out_file, '--show_format',
                '--output_file_type', "FieldTable"]

        # Capture stdout for the required configuration settings
        outstring = io.StringIO()
        with redirect_stdout(outstring):
            set_config.create_config_obj(args)
        result = outstring.getvalue()

        assert result == outcome

def test_values_needed_yaml(): #pylint: disable=unused-variable
    '''Test that the values_needed flag logs keys completed, keys containing  
    unfilled jinja2 templates, and keys set to empty'''

    input_file = os.path.join(uwtools_file_base, pathlib.Path("fixtures/srw_example.yaml"))
    args = ['-i', input_file, '--values_needed']

    # Capture stdout for values_needed output
    outstring = io.StringIO()
    with redirect_stdout(outstring):
        set_config.create_config_obj(args)
    result = outstring.getvalue()
    outcome=\
    """Keys that are complete:
    FV3GFS
    FV3GFS.nomads
    FV3GFS.nomads.protocol
    FV3GFS.nomads.file_names
    FV3GFS.nomads.file_names.grib2
    FV3GFS.nomads.file_names.testfalse
    FV3GFS.nomads.file_names.testzero

Keys that have unfilled jinja2 templates:
    FV3GFS.nomads.url: https://nomads.ncep.noaa.gov/pub/data/nccf/com/gfs/prod/gfs.{{ yyyymmdd }}/{{ hh }}/atmos
    FV3GFS.nomads.file_names.grib2.anl: ['gfs.t{{ hh }}z.atmanl.nemsio','gfs.t{{ hh }}z.sfcanl.nemsio']
    FV3GFS.nomads.file_names.grib2.fcst: ['gfs.t{{ hh }}z.pgrb2.0p25.f{{ fcst_hr03d }}']

Keys that are set to empty:
    FV3GFS.nomads.file_names.nemsio
    FV3GFS.nomads.testempty
"""
    assert result == outcome

def test_values_needed_ini(): #pylint: disable=unused-variable
    '''Test that the values_needed flag logs keys completed, keys containing  
    unfilled jinja2 templates, and keys set to empty'''

    input_file = os.path.join(uwtools_file_base, pathlib.Path("fixtures/simple3.ini"))
    args = ['-i', input_file, '--values_needed']

    # Capture stdout for values_needed output
    outstring = io.StringIO()
    with redirect_stdout(outstring):
        set_config.create_config_obj(args)
    result = outstring.getvalue()

    outcome=\
    """Keys that are complete:
    salad
    salad.base
    salad.fruit
    salad.vegetable
    salad.dressing
    dessert
    dessert.type
    dessert.side
    dessert.servings

Keys that have unfilled jinja2 templates:
    salad.how_many: {{amount}}
    dessert.flavor: {{flavor}}

Keys that are set to empty:
    salad.toppings
    salad.meat
"""
    assert result == outcome

def test_values_needed_f90nml(): #pylint: disable=unused-variable
    '''Test that the values_needed flag logs keys completed, keys containing  
    unfilled jinja2 templates, and keys set to empty'''

    input_file = os.path.join(uwtools_file_base, pathlib.Path("fixtures/simple3.nml"))
    args = ['-i', input_file, '--values_needed']

    outstring = io.StringIO()
    with redirect_stdout(outstring):
        set_config.create_config_obj(args)
    result = outstring.getvalue()

    outcome=\
        """Keys that are complete:
    salad
    salad.base
    salad.fruit
    salad.vegetable
    salad.how_many
    salad.extras
    salad.dessert

Keys that have unfilled jinja2 templates:
    salad.dressing: {{ dressing }}

Keys that are set to empty:
    salad.toppings
    salad.appetizer
"""
    assert result == outcome


def test_cfg_to_yaml():
    ''' testing that .cfg file can be used to create a yaml object.'''
    input_file = os.path.join(uwtools_file_base, pathlib.Path("fixtures/simple2.cfg"))

    with tempfile.TemporaryDirectory(dir='.') as tmp_dir:

        out_file = f'{tmp_dir}/test.yaml'
        args = ['-i', input_file, '--dry_run', '--input_file_type', '.yaml']

        outstring = io.StringIO()
        with redirect_stdout(outstring):
            set_config.create_config_obj(args)
        result = outstring.getvalue()

        expected = config.YAMLConfig(input_file)
        expected_file = f'{tmp_dir}/test.yaml'
        expected.dump_file(expected_file)

        assert result.rstrip('\n') == str(expected)

def test_cfg_to_yaml_conversion(): #pylint: disable=unused-variable
    ''' Test that a .cfg file can be used to create a yaml object.'''
    input_file = os.path.join(uwtools_file_base, pathlib.Path("fixtures/srw_example_yaml.cfg"))

    with tempfile.TemporaryDirectory(dir='.') as tmp_dir:

        out_file = f'{tmp_dir}/test_ouput.yaml'
        args = ['-i', input_file, '-o', out_file, '--input_file_type', 'YAML']

        set_config.create_config_obj(args)

        expected = config.YAMLConfig(input_file)
        expected_file = f'{tmp_dir}/test.yaml'
        expected.dereference_all()
        expected.dump_file(expected_file)

        assert compare_files(expected_file, out_file)

        with open(out_file, 'r', encoding='utf-8') as output:
            assert output.read()[-1] == '\n'

def test_output_file_conversion(): #pylint: disable=unused-variable
    ''' Test that --output_input_type converts config object to desired object type'''
    input_file = os.path.join(uwtools_file_base, pathlib.Path("fixtures/simple.nml"))

    with tempfile.TemporaryDirectory(dir='.') as tmp_dir:

        out_file = f'{tmp_dir}/test_ouput.cfg'
        args = ['-i', input_file, '-o', out_file, '--output_file_type',
                'F90']

        set_config.create_config_obj(args)

        expected = config.F90Config(input_file)
        expected_file = f'{tmp_dir}/expected_nml.nml'
        expected.dump_file(expected_file)

        assert compare_files(expected_file, out_file)

        with open(out_file, 'r', encoding='utf-8') as output:
            assert output.read()[-1] == '\n'

def test_config_file_conversion(): #pylint: disable=unused-variable
    ''' Test that --config_input_type converts config object to desired object type'''
    input_file = os.path.join(uwtools_file_base, pathlib.Path("fixtures/simple2.nml"))
    config_file = os.path.join(uwtools_file_base, pathlib.Path("fixtures/simple2.ini"))

    with tempfile.TemporaryDirectory(dir='.') as tmp_dir:

        out_file = f'{tmp_dir}/test_config_conversion.nml'
        args = ['-i', input_file, '-c', config_file, '-o', out_file, '--config_file_type', 'F90']

        set_config.create_config_obj(args)

        expected = config.F90Config(input_file)
        config_file_obj = config.F90Config(config_file)
        expected.update_values(config_file_obj)
        expected_file = f'{tmp_dir}/expected_nml.nml'
        expected.dump_file(expected_file)

        assert compare_files(expected_file, out_file)

        with open(out_file, 'r', encoding='utf-8') as output:
            assert output.read()[-1] == '\n'

def test_erroneous_conversion_flags(): #pylint: disable=unused-variable
    ''' Test that error is thrown when conversion file types are not compatible'''

    with tempfile.TemporaryDirectory(dir='.') as tmp_dir:

        # test --input_file_type
        input_file = os.path.join(uwtools_file_base, pathlib.Path("fixtures/simple2_nml.cfg"))
        args = ['-i', input_file, '--input_file_type', ".pdf"]

        with pytest.raises(SystemExit):
            set_config.create_config_obj(args)

        # test --config_file_type
        input_file = os.path.join(uwtools_file_base, pathlib.Path("fixtures/simple2.nml"))
        config_file = os.path.join(uwtools_file_base, pathlib.Path("fixtures/srw_example.yaml"))
        args = ['-i', input_file, '-c', config_file, '--config_file_type', "YAML"]

        with pytest.raises(ValueError):
            set_config.create_config_obj(args)

        # test --ouput_file_type
        input_file = os.path.join(uwtools_file_base, pathlib.Path("fixtures/srw_example.yaml"))
        out_file = f'{tmp_dir}/test_outfile_conversion.yaml'
        args = ['-i', input_file, '-o', out_file, '--output_file_type', "F90"]

        with pytest.raises(ValueError):
            set_config.create_config_obj(args)
