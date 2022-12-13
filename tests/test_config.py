'''
Set of test for loading YAML files using the function call load_yaml
'''
#pylint: disable=unused-variable
from collections import OrderedDict
import datetime
import filecmp
import os
import pathlib
import tempfile
import json
import itertools

from uwtools import config

uwtools_file_base = os.path.join(os.path.dirname(__file__))

def test_yaml_config_simple():
    '''Test that YAML load, update, and dump work with a basic YAML file. '''

    test_yaml = os.path.join(uwtools_file_base,pathlib.Path("fixtures/simple.yaml"))
    cfg = config.YAMLConfig(test_yaml)

    expected = {
        "scheduler": "slurm",
        "jobname": "abcd",
        "extra_stuff": 12345,
        "account": "user_account",
        "nodes": 1,
        "queue": "bos",
        "tasks_per_node": 4,
        "walltime": "00:01:00",
    }
    assert cfg == expected
    assert repr(cfg.data) == json.dumps(expected).replace('"', "'")

    with tempfile.TemporaryDirectory(dir='.') as tmp_dir:
        out_file = f'{tmp_dir}/test_yaml_dump.yml'
        cfg.dump_file(out_file)
        assert filecmp.cmp(test_yaml, out_file)

    cfg.update({'nodes': 12})
    expected['nodes'] = 12

    assert cfg == expected

def test_yaml_config_composite_types():
    ''' Test that YAML load and dump work with a YAML file that has
    multiple data structures and levels. '''

    test_yaml = os.path.join(uwtools_file_base,pathlib.Path("fixtures/result4.yaml"))
    cfg = config.YAMLConfig(test_yaml)

    assert cfg.get('step_cycle') == 'PT6H'
    assert isinstance(cfg.get('init_cycle'), datetime.datetime)

    generic_repos = cfg.get('generic_repos')
    assert isinstance(generic_repos, list)
    assert isinstance(generic_repos[0], dict)
    assert generic_repos[0].get('branch') == 'develop'

    models = cfg.get('models')
    assert models[0].get('config').get('vertical_resolution') == 64

def test_yaml_config_include_files():

    ''' Test that including files via the !INCLUDE constructor works as
    expected. '''

    test_yaml = os.path.join(uwtools_file_base,pathlib.Path("fixtures/include_files.yaml"))
    cfg = config.YAMLConfig(test_yaml)

    # salad key tests loading one file. there should be 4 items under salad
    assert cfg['salad'].get('fruit') == 'papaya'
    assert cfg['salad'].get('how_many') == 17
    assert len(cfg['salad']) == 4


    # two_files key tests loading a list of files, and that values are updated
    # to the last read in. There should be 7 items under two_files
    assert cfg['two_files'].get('fruit') == 'papaya'
    assert cfg['two_files'].get('vegetable') == 'peas'
    assert len(cfg['two_files']) == 7

    # reverse_files tests loading a list of files in the reverse order as above,
    # and that the values are updated to the last read in.
    assert cfg['reverse_files'].get('vegetable') == 'eggplant'

def test_f90nml_config_simple():
    '''Test that f90nml load, update, and dump work with a basic f90 namelist file. '''

    test_nml = os.path.join(uwtools_file_base,pathlib.Path("fixtures/simple.nml"))
    cfg = config.F90Config(test_nml)

    expected = {
        "salad": OrderedDict({
            "base": "kale",
            "fruit": "banana",
            "vegetable": "tomato",
            "how_many": 12,
            "dressing": "balsamic",
            })
    }
    assert cfg == expected

    with tempfile.TemporaryDirectory(dir='.') as tmp_dir:
        out_file = f'{tmp_dir}/test_nml_dump.nml'
        cfg.dump_file(out_file)

        assert filecmp.cmp(test_nml, out_file)

    cfg.update({'dressing': ['ranch', 'italian']})
    expected['dressing'] = ['ranch', 'italian']

    assert cfg == expected


def test_ini_config_simple():
    '''Test that INI config load and dump work with a basic INI file.
    Everything in INI is treated as a string!
    '''

    test_ini = os.path.join(uwtools_file_base,pathlib.Path("fixtures/simple.ini"))
    cfg = config.INIConfig(test_ini)

    expected = {
        "salad": {
            "base": "kale",
            "fruit": "banana",
            "vegetable": "tomato",
            "how_many": "12",
            "dressing": "balsamic",
            }
    }
    assert cfg == expected

    with tempfile.TemporaryDirectory(dir='.') as tmp_dir:
        out_file = f'{tmp_dir}/test_ini_dump.ini'
        cfg.dump_file(out_file)

        assert filecmp.cmp(test_ini, out_file)

    cfg.update({'dressing': ['ranch', 'italian']})
    expected['dressing'] = ['ranch', 'italian']
    assert cfg == expected

def test_ini_config_bash():

    '''Test that INI config load and dump work with a basic bash file.
    '''

    test_bash = os.path.join(uwtools_file_base,pathlib.Path("fixtures/simple.sh"))
    cfg = config.INIConfig(test_bash, space_around_delimiters=False)

    expected = {
        "base": "kale",
        "fruit": "banana",
        "vegetable": "tomato",
        "how_many": "12",
        "dressing": "balsamic",
    }
    assert cfg == expected

    with tempfile.TemporaryDirectory(dir='.') as tmp_dir:
        out_file = f'{tmp_dir}/test_bash_dump.sh'
        cfg.dump_file(out_file)

        assert filecmp.cmp(test_bash, out_file)

    cfg.update({'dressing': ['ranch', 'italian']})
    expected['dressing'] = ['ranch', 'italian']
    assert cfg == expected

def test_transform_config():
    '''Test that transforms work as intended.

    '''
    for test1, test2 in itertools.permutations(["INI", "YAML", "F90"],2):
        test1file = "NML" if test1 == "F90" else test1
        test2file = "NML" if test2 == "F90" else test2

        test = os.path.join(uwtools_file_base,pathlib.Path("fixtures",f"simple.{test1file.lower()}"))
        ref = os.path.join(uwtools_file_base,pathlib.Path("fixtures",f"simple.{test2file.lower()}"))

        cfgin = getattr(config, f"{test1}Config")
        cfg = cfgin(test)
        cfgout = getattr(config, f"{test2}Config")

        with tempfile.TemporaryDirectory(dir='.') as tmp_dir:
            out_file = f'{tmp_dir}/test_{test1.lower()}to{test2.lower()}_dump.{test2file.lower()}'
            cfgout.dump_file(cfg, out_file)

            assert filecmp.cmp(ref, out_file)
