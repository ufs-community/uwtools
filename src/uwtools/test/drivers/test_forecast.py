"""
Tests for forecast driver
"""

# import glob
# import os
# import pathlib
# import shutil

# import pytest

from uwtools import config
from uwtools.drivers.forecast import FV3Forecast
from uwtools.test.support import fixture_posix
from uwtools.utils import file_helpers


def test_create_config(tmp_path):
    """Test that providing a yaml base input file and a config file will
    create and update yaml config file"""

    input_file = fixture_posix("fruit_config.yaml")
    config_file = fixture_posix("fruit_config_similar.yaml")
    output_file = (tmp_path / "test_config_from_yaml.yaml").as_posix()

    forecast_obj = FV3Forecast()
    forecast_obj.create_model_config(config_file, output_file, input_file)

    expected = config.YAMLConfig(input_file)
    expected.update_values(config.YAMLConfig(config_file))
    expected_file = tmp_path / "expected_yaml.yaml"
    expected.dump_file(expected_file)

    assert file_helpers.compare_files(expected_file, output_file)


def test_create_namelist(tmp_path):
    """Tests create_namelist method with and without optional base file"""

    forecast_obj = FV3Forecast()
    update_obj = config.F90Config(fixture_posix("simple.nml"))
    outnml_file = tmp_path / "create_out.nml"

    expected_1 = """&salad
    base = 'kale'
    fruit = 'banana'
    vegetable = 'tomato'
    how_many = 12
    dressing = 'balsamic'
/
"""
    forecast_obj.create_namelist(update_obj, str(outnml_file))
    with open(outnml_file, "r", encoding="utf-8") as out_file:
        outnml_string = out_file.read()
    assert outnml_string == expected_1

    expected_2 = """&salad
    base = 'kale'
    fruit = 'banana'
    vegetable = 'tomato'
    how_many = 12
    dressing = 'balsamic'
    toppings = ,
    extras = 0
    dessert = .false.
    appetizer = ,
/
"""
    base_file = fixture_posix("simple3.nml")
    forecast_obj.create_namelist(update_obj, outnml_file, base_file)
    with open(outnml_file, "r", encoding="utf-8") as out_file:
        outnml_string = out_file.read()
    assert outnml_string == expected_2


def test_create_field_table(tmp_path):
    """Tests create_field_table method with and without optional base file"""

    forecast_obj = FV3Forecast()
    update_obj = config.YAMLConfig(fixture_posix("FV3_GFS_v16_update.yaml"))

    outfldtbl_file_1 = tmp_path / "field_table_one.FV3_GFS"
    expected_1 = fixture_posix("field_table_from_input.FV3_GFS")
    forecast_obj.create_field_table(update_obj, outfldtbl_file_1)
    assert file_helpers.compare_files(expected_1, outfldtbl_file_1)

    base_file = fixture_posix("FV3_GFS_v16.yaml")
    outfldtbl_file_2 = tmp_path / "field_table_two.FV3_GFS"
    expected_2 = fixture_posix("field_table_from_base.FV3_GFS")
    forecast_obj.create_field_table(update_obj, outfldtbl_file_2, base_file)
    assert file_helpers.compare_files(expected_2, outfldtbl_file_2)


# def test_create_directory_structure():
#     """Tests create_directory_structure method given a directory."""
#     forecast_obj = FV3Forecast()

#     with tempfile.TemporaryDirectory() as run_directory:
#         # Test create_directory_structure when run directory does not exist
#         forecast_obj.create_directory_structure(run_directory, "delete")
#         assert os.path.isdir(os.path.join(run_directory, "RESTART"))

#         # Put a test file into the run directory
#         test_file = os.path.join(run_directory, "test.txt")
#         with open(test_file, "w", encoding="utf-8") as file_open:
#             file_open.write("test file")
#             file_open.close()

#         # Test create_directory_structure when run directory does exist
#         forecast_obj.create_directory_structure(run_directory, "delete")
#         assert os.path.isdir(os.path.join(run_directory, "RESTART"))
#         # Test file should be gone after delete
#         assert not os.path.isfile(test_file)

#         # Test create_directory_structure when run directory does exist
#         forecast_obj.create_directory_structure(run_directory, "rename")
#         copy_directory = glob.glob(run_directory + "_*")[0]
#         assert os.path.isdir(os.path.join(copy_directory, "RESTART"))

#         # Clean up copied directory fronm rename
#         if os.path.isdir(copy_directory):
#             shutil.rmtree(copy_directory)

#         # Test create_directory_structure when run directory does exist
#         with pytest.raises(SystemExit) as pytest_wrapped_e:
#             forecast_obj.create_directory_structure(run_directory, "quit")
#         assert pytest_wrapped_e.type == SystemExit
#         assert pytest_wrapped_e.value.code == 1
