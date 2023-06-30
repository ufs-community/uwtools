# pylint: disable=missing-function-docstring,redefined-outer-name

"""
Tests for forecast driver
"""

from pytest import fixture, raises

from uwtools import config
from uwtools.drivers.forecast import FV3Forecast
from uwtools.tests.support import compare_files, fixture_path


def test_create_config(tmp_path):
    """Test that providing a yaml base input file and a config file will
    create and update yaml config file"""

    input_file = fixture_path("fruit_config.yaml")
    config_file = fixture_path("fruit_config_similar.yaml")
    output_file = (tmp_path / "test_config_from_yaml.yaml").as_posix()

    forecast_obj = FV3Forecast()
    forecast_obj.create_model_config(config_file, output_file, input_file)

    expected = config.YAMLConfig(input_file)
    expected.update_values(config.YAMLConfig(config_file))
    expected_file = tmp_path / "expected_yaml.yaml"
    expected.dump_file(expected_file)

    assert compare_files(expected_file, output_file)


def test_create_directory_structure(tmp_path):
    """Tests create_directory_structure method given a directory."""

    rundir = tmp_path / "rundir"
    forecast_obj = FV3Forecast()

    # Test delete behavior when run directory does not exist.
    forecast_obj.create_directory_structure(rundir, "delete")
    assert (rundir / "RESTART").is_dir()

    # Create a file in the run directory.
    test_file = rundir / "test.txt"
    with open(test_file, "w", encoding="utf-8"):
        pass
    assert test_file.is_file()

    # Test delete behavior when run directory exists. Test file should be gone
    # since old run directory was deleted.
    forecast_obj.create_directory_structure(rundir, "delete")
    assert (rundir / "RESTART").is_dir()
    assert not test_file.is_file()

    # Test rename behavior when run directory exists.
    forecast_obj.create_directory_structure(rundir, "rename")
    copy_directory = next(tmp_path.glob("%s_*" % rundir.name))
    assert (copy_directory / "RESTART").is_dir()

    # Test quit behavior when run directory exists.
    with raises(SystemExit) as pytest_wrapped_e:
        forecast_obj.create_directory_structure(rundir, "quit")
    assert pytest_wrapped_e.type == SystemExit
    assert pytest_wrapped_e.value.code == 1


@fixture
def create_field_table_assets():
    return FV3Forecast(), config.YAMLConfig(fixture_path("FV3_GFS_v16_update.yaml"))


def test_create_field_table_with_base_file(create_field_table_assets, tmp_path):
    """Tests create_field_table method with optional base file"""
    forecast_obj, update_obj = create_field_table_assets
    base_file = fixture_path("FV3_GFS_v16.yaml")
    outfldtbl_file = tmp_path / "field_table_two.FV3_GFS"
    expected = fixture_path("field_table_from_base.FV3_GFS")
    forecast_obj.create_field_table(update_obj, outfldtbl_file, base_file)
    assert compare_files(expected, outfldtbl_file)


def test_create_field_table_without_base_file(create_field_table_assets, tmp_path):
    """Tests create_field_table without optional base file"""
    forecast_obj, update_obj = create_field_table_assets
    outfldtbl_file = tmp_path / "field_table_one.FV3_GFS"
    expected = fixture_path("field_table_from_input.FV3_GFS")
    forecast_obj.create_field_table(update_obj, outfldtbl_file)
    assert compare_files(expected, outfldtbl_file)


@fixture
def create_namelist_assets(tmp_path):
    return FV3Forecast(), config.F90Config(fixture_path("simple.nml")), tmp_path / "create_out.nml"


def test_create_namelist_with_base_file(create_namelist_assets):
    """Tests create_namelist method with optional base file"""
    forecast_obj, update_obj, outnml_file = create_namelist_assets
    base_file = fixture_path("simple3.nml")
    forecast_obj.create_namelist(update_obj, outnml_file, base_file)
    expected = """
&salad
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
""".lstrip()
    with open(outnml_file, "r", encoding="utf-8") as out_file:
        assert out_file.read() == expected


def test_create_namelist_without_base_file(create_namelist_assets):
    """Tests create_namelist method without optional base file"""
    forecast_obj, update_obj, outnml_file = create_namelist_assets
    forecast_obj.create_namelist(update_obj, str(outnml_file))
    expected = """
&salad
    base = 'kale'
    fruit = 'banana'
    vegetable = 'tomato'
    how_many = 12
    dressing = 'balsamic'
/
""".lstrip()
    with open(outnml_file, "r", encoding="utf-8") as out_file:
        assert out_file.read() == expected
