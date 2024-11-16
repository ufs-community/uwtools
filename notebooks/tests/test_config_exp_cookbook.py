from testbook import testbook


def test_config_exp():
    with open("fixtures/config-exp/base-file.yaml", "r", encoding="utf-8") as f:
        base_cfg = f.read().rstrip()
    with open("fixtures/config-exp/hrrr-ics.yaml", "r", encoding="utf-8") as f:
        hrrr_ics = f.read().rstrip()
    with open("fixtures/config-exp/fv3-rap-physics.yaml", "r", encoding="utf-8") as f:
        fv3_rap_phys = f.read().rstrip()
    with open("fixtures/config-exp/user.yaml", "r", encoding="utf-8") as f:
        user_cfg = f.read().rstrip()
    with testbook("config-exp-cookbook.ipynb", execute=True) as tb:
        assert tb.cell_output_text(1) == ""
        assert tb.cell_output_text(2) == base_cfg
        assert tb.cell_output_text(4) == hrrr_ics
        assert tb.cell_output_text(6) == fv3_rap_phys
        assert tb.cell_output_text(8) == user_cfg
        assert tb.cell_output_text(10) == ""
        updated_cfg = (
            "ACCOUNT: zrtrr",
            "convert_nst: false",
            "data_dir_input_grid: /path/to/my/output/make_ics",
            "varmap_file: /path/to/ufs-srweather-app/parm/",
            "rundir: /path/to/my/output/make_ics",
        )
        assert all(x in tb.cell_output_text(12) for x in updated_cfg)
        validate_out = (
            "INFO Validating config against internal schema: chgres-cube",
            "INFO 0 UW schema-validation errors found",
            "INFO Validating config against internal schema: platform",
            "chgres_cube valid schema: State: Ready",
        )
        assert all(x in tb.cell_output_text(14) for x in validate_out)
