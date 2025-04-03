from pathlib import Path

from pytest import fixture
from testbook import testbook
from uwtools.config.formats.yaml import YAMLConfig

base = Path("fixtures/exp-config")


@fixture(scope="module")
def tb():
    with testbook("exp-config-cb.ipynb", execute=True) as tb:
        yield tb


def test_exp_config_cb(load, tb):
    assert tb.cell_output_text(1) == ""
    assert tb.cell_output_text(3) == load(base / "base-file.yaml")
    assert tb.cell_output_text(5) == load(base / "fv3-rap-physics.yaml")
    assert tb.cell_output_text(7) == load(base / "user.yaml")
    assert tb.cell_output_text(9) == str(YAMLConfig(base / "base-file.yaml"))
    for line in [
        "cycle_day: !int \"{{ cycle.strftime('%d') }}\"",
        "varmap_file: '{{ user.PARMdir }}/ufs_utils/varmap_tables/GSDphys_var_map.txt'",
        "PARMdir: /path/to/ufs-srweather-app/parm",
    ]:
        assert line in tb.cell_output_text(11)
    deref_cfg = (
        "data_dir_input_grid: /path/to/my/output/make_ics",
        "rundir: /path/to/my/output/make_ics",
    )
    assert all(x in tb.cell_output_text(13) for x in deref_cfg)
    for line in [
        "Validating config against internal schema: chgres-cube",
        "0 schema-validation errors found in chgres_cube config",
        "Validating config against internal schema: platform",
        "0 schema-validation errors found in platform config",
        "chgres_cube valid schema: Ready",
    ]:
        assert line in tb.cell_output_text(15)
