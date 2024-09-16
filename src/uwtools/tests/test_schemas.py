# pylint: disable=missing-function-docstring,redefined-outer-name
"""
Granular tests of JSON Schema schemas.
"""

from functools import partial

from pytest import fixture, mark

from uwtools.tests.support import schema_validator, with_del, with_set

# Fixtures


CDEPS_CONFIG = {
    "atm_in": {
        "base_file": "/path/to/atm.nml",
        "update_values": {
            "datm_nml": {
                "anomaly_forcing": "string",
                "bias_correct": "string",
                "datamode": "GFS",
                "export_all": True,
                "factorfn_data": "string",
                "factorfn_mesh": "string",
                "flds_co2": True,
                "flds_presaero": True,
                "flds_presndep": True,
                "flds_wiso": True,
                "flds_preso3": True,
                "iradsw": 1,
                "model_maskfile": "string",
                "model_meshfile": "string",
                "nx_global": 1,
                "ny_global": 1,
                "restfilm": "string",
                "skip_restart_read": True,
            },
        },
    },
    "atm_streams": {
        "streams": {
            "stream01": {
                "dtlimit": 1.5,
                "mapalgo": "string",
                "readmode": "single",
                "stream_data_files": ["string", "string"],
                "stream_data_variables": ["string", "string"],
                "stream_lev_dimname": "string",
                "stream_mesh_file": "string",
                "stream_offset": 1,
                "stream_vectors": ["u", "v"],
                "taxmode": "string",
                "tinterpalgo": "string",
                "yearAlign": 1,
                "yearFirst": 1,
                "yearLast": 1,
            }
        },
        "template_file": "/path/to/atm.jinja2",
    },
    "ocn_in": {
        "base_file": "/path/to/ocn.nml",
        "update_values": {
            "docn_nml": {
                "datamode": "string",
                "import_data_fields": "string",
                "model_maskfile": "string",
                "model_meshfile": "string",
                "nx_global": 1,
                "ny_global": 1,
                "restfilm": "string",
                "skip_restart_read": True,
                "sst_constant_value": 3.14,
            },
        },
    },
    "ocn_streams": {
        "streams": {
            "stream01": {
                "dtlimit": 1.5,
                "mapalgo": "string",
                "readmode": "single",
                "stream_data_files": ["string", "string"],
                "stream_data_variables": ["string", "string"],
                "stream_lev_dimname": "string",
                "stream_mesh_file": "string",
                "stream_offset": 1,
                "stream_vectors": ["u", "v"],
                "taxmode": "string",
                "tinterpalgo": "string",
                "yearAlign": 1,
                "yearFirst": 1,
                "yearLast": 1,
            }
        },
        "template_file": "/path/to/atm.jinja2",
    },
    "rundir": "/path/to/run/dir",
}


@fixture
def cdeps_config():
    return CDEPS_CONFIG


@fixture
def chgres_cube_config():
    return {
        "execution": {
            "executable": "chgres_cube",
        },
        "namelist": {
            "base_file": "/path",
            "update_values": {
                "config": {
                    "atm_core_files_input_grid": ["a1", "a2"],
                    "atm_files_input_grid": ["b1", "b2"],
                    "atm_tracer_files_input_grid": ["c1", "c2"],
                    "atm_weight_file": "d",
                    "convert_atm": True,
                    "convert_nst": True,
                    "convert_sfc": True,
                    "cycle_day": 1,
                    "cycle_hour": 2,
                    "cycle_mon": 3,
                    "cycle_year": 4,
                    "data_dir_input_grid": "e",
                    "external_model": "GFS",
                    "fix_dir_target_grid": "f",
                    "geogrid_file_input_grid": "g",
                    "grib2_file_input_grid": "h",
                    "halo_blend": 5,
                    "halo_bndy": 6,
                    "input_type": "grib2",
                    "lai_from_climo": True,
                    "minmax_vgfrc_from_climo": True,
                    "mosaic_file_input_grid": "i",
                    "mosaic_file_target_grid": "j",
                    "nsoill_out": 7,
                    "nst_files_input_grid": ["k1", "k2"],
                    "orog_dir_input_grid": "l",
                    "orog_dir_target_grid": "m",
                    "orog_files_input_grid": ["n1", "n2"],
                    "orog_files_target_grid": ["o1", "o2"],
                    "regional": 8,
                    "sfc_files_input_grid": ["p1", "p2"],
                    "sotyp_from_climo": True,
                    "tg3_from_soil": True,
                    "thomp_mp_climo_file": "q",
                    "tracers": ["r1", "r2"],
                    "tracers_input": ["s1", "s2"],
                    "varmap_file": "t",
                    "vcoord_file_target_grid": "u",
                    "vgfrc_from_climo": True,
                    "vgtyp_from_climo": True,
                    "wam_cold_start": True,
                    "wam_parm_file": "v",
                }
            },
            "validate": True,
        },
        "rundir": "/tmp",
    }


@fixture
def chgres_cube_prop():
    return partial(schema_validator, "chgres-cube", "properties", "chgres_cube", "properties")


@fixture
def esg_grid_prop():
    return partial(schema_validator, "esg-grid", "properties", "esg_grid", "properties")


@fixture
def esg_namelist():
    return {
        "base_file": "/some/path",
        "update_values": {
            "regional_grid_nml": {
                "delx": 0.22,
                "dely": 0.22,
                "lx": -200,
                "ly": -130,
                "pazi": 0.0,
                "plat": 45.5,
                "plon": -100.5,
            },
        },
        "validate": True,
    }


@fixture
def fv3_prop():
    return partial(schema_validator, "fv3", "properties", "fv3", "properties")


@fixture
def global_equiv_resol_prop():
    return partial(
        schema_validator, "global-equiv-resol", "properties", "global_equiv_resol", "properties"
    )


@fixture
def ioda_prop():
    return partial(schema_validator, "ioda", "properties", "ioda", "properties")


@fixture
def jedi_prop():
    return partial(schema_validator, "jedi", "properties", "jedi", "properties")


@fixture
def make_hgrid_prop():
    return partial(schema_validator, "make-hgrid", "properties", "make_hgrid", "properties")


@fixture
def make_solo_mosaic_prop():
    return partial(
        schema_validator, "make-solo-mosaic", "properties", "make_solo_mosaic", "properties"
    )


@fixture
def mpas_prop():
    return partial(schema_validator, "mpas", "properties", "mpas", "properties")


@fixture
def mpas_init_prop():
    return partial(schema_validator, "mpas-init", "properties", "mpas_init", "properties")


@fixture
def mpas_streams():
    return {
        "input": {
            "filename_template": "init.nc",
            "input_interval": "initial_only",
            "mutable": False,
            "type": "input",
        },
        "output": {
            "clobber_mode": "overwrite",
            "filename_interval": "input_interval",
            "filename_template": "output.$Y-$M-$D $h.$m.$s.nc",
            "files": ["f1", "f2"],
            "io_type": "netcdf4",
            "mutable": True,
            "output_interval": "6:00:00",
            "packages": "pkg",
            "precision": "double",
            "reference_time": "2014-01-01 00:00:00",
            "streams": ["s1", "s2"],
            "type": "output",
            "var_arrays": ["va1", "va2"],
            "var_structs": ["vs1", "vs2"],
            "vars": ["v1", "v2"],
        },
    }


@fixture
def sfc_climo_gen_prop():
    return partial(schema_validator, "sfc-climo-gen", "properties", "sfc_climo_gen", "properties")


@fixture
def schism_prop():
    return partial(schema_validator, "schism", "properties", "schism", "properties")


@fixture
def shave_prop():
    return partial(schema_validator, "shave", "properties", "shave", "properties")


@fixture
def ungrib_prop():
    return partial(schema_validator, "ungrib", "properties", "ungrib", "properties")


@fixture
def upp_prop():
    return partial(schema_validator, "upp", "properties", "upp", "properties")


@fixture
def ww3_prop():
    return partial(schema_validator, "ww3", "properties", "ww3", "properties")


# batchargs


def test_schema_batchargs():
    errors = schema_validator("batchargs")
    # Basic correctness, only walltime is required:
    assert "'walltime' is a required property" in errors({})
    assert not errors({"walltime": "00:05:00"})
    # Managed properties are fine:
    assert not errors({"queue": "string", "walltime": "00:05:00"})
    # But so are unknown ones:
    assert not errors({"--foo": 42, "walltime": "00:05:00"})
    # It just has to be a map:
    assert "[] is not of type 'object'\n" in errors([])
    # The "threads" argument is not allowed: It will be propagated, if set, from execution.threads.
    assert "should not be valid" in errors({"threads": 4, "walltime": "00:05:00"})
    # Some keys require boolean values:
    for key in ["debug", "exclusive"]:
        assert "is not of type 'boolean'\n" in errors({key: None})
    # Some keys require integer values:
    for key in ["cores", "nodes"]:
        assert "is not of type 'integer'\n" in errors({key: None})
    # Some keys require string values:
    for key in [
        "export",
        "jobname",
        "memory",
        "partition",
        "queue",
        "rundir",
        "shell",
        "stderr",
        "stdout",
        "walltime",
    ]:
        assert "is not of type 'string'\n" in errors({key: None})


# cdeps


def test_schema_cdeps(cdeps_config):
    errors = schema_validator("cdeps", "properties", "cdeps")
    # Basic correctness:
    assert not errors(cdeps_config)
    # All top-level keys are optional:
    for key in ["atm_in", "atm_streams", "ocn_in", "ocn_streams"]:
        assert not errors(with_del(cdeps_config, key))
    # Additional top-level keys are not allowed:
    assert "Additional properties are not allowed" in errors(with_set(cdeps_config, "bar", "foo"))


def test_schema_cdeps_atm_in(cdeps_config):
    block = cdeps_config["atm_in"]
    errors = schema_validator("cdeps", "properties", "cdeps", "properties", "atm_in")
    # Namelist values must be of the correct types:
    nmlerr = lambda k, v: errors(with_set(block, v, "update_values", "datm_nml", k))
    # boolean:
    ks_boolean = [
        "export_all",
        "flds_co2",
        "flds_presaero",
        "flds_presndep",
        "flds_preso3",
        "flds_wiso",
        "skip_restart_read",
    ]
    for k in ks_boolean:
        assert "is not of type 'boolean'\n" in nmlerr(k, None)
    # integer:
    ks_integer = ["iradsw", "nx_global", "ny_global"]
    for k in ks_integer:
        assert "is not of type 'integer'\n" in nmlerr(k, None)
    # enum:
    ks_enum = ["datamode"]
    assert "is not one of" in nmlerr("datamode", None)
    # string:
    ks_string = [
        "anomaly_forcing",
        "bias_correct",
        "factorfn_data",
        "factorfn_mesh",
        "model_maskfile",
        "model_meshfile",
        "restfilm",
    ]
    for k in ks_string:
        assert "is not of type 'string'\n" in nmlerr(k, None)
    # All namelist keys are optional:
    for k in ks_boolean + ks_integer + ks_enum + ks_string:
        assert not errors(with_del(block, "update_values", "datm_nml", k))


@mark.parametrize("section", ["atm", "ocn"])
def test_schema_cdeps_nml_common(cdeps_config, section):
    block = cdeps_config[f"{section}_in"]
    errors = schema_validator("cdeps", "properties", "cdeps", "properties", f"{section}_in")
    # Either base_file or update_values is sufficient:
    for k in ["base_file", "update_values"]:
        assert not errors(with_del(block, k))
    # At least one is required:
    assert "is not valid" in errors(with_del(with_del(block, "base_file"), "update_values"))
    # The base_file value must be a string:
    assert "is not of type 'string'\n" in errors(with_set(block, 1, "base_file"))
    # The update_values.datm_nml value is required:
    assert f"'d{section}_nml' is a required property" in errors(
        with_del(block, "update_values", f"d{section}_nml")
    )
    # Additional namelists are not allowed:
    assert not errors(with_set(block, {}, "update_values", "another_namelist"))


def test_schema_cdeps_ocn_in(cdeps_config):
    block = cdeps_config["ocn_in"]
    errors = schema_validator("cdeps", "properties", "cdeps", "properties", "ocn_in")
    # Namelist values must be of the correct types:
    nmlerr = lambda k, v: errors(with_set(block, v, "update_values", "docn_nml", k))
    # boolean:
    ks_boolean = ["skip_restart_read"]
    for k in ks_boolean:
        assert "is not of type 'boolean'\n" in nmlerr(k, None)
    # integer:
    ks_integer = ["nx_global", "ny_global"]
    for k in ks_integer:
        assert "is not of type 'integer'\n" in nmlerr(k, None)
    # number:
    ks_number = ["sst_constant_value"]
    for k in ks_number:
        assert "is not of type 'number'\n" in nmlerr(k, None)
    # string:
    ks_string = [
        "datamode",
        "import_data_fields",
        "model_maskfile",
        "model_meshfile",
        "restfilm",
    ]
    for k in ks_string:
        assert "is not of type 'string'\n" in nmlerr(k, None)
    # All namelist keys are optional:
    for k in ks_boolean + ks_integer + ks_number + ks_string:
        assert not errors(with_del(block, "update_values", "docn_nml", k))


@mark.parametrize("section", ["atm", "ocn"])
def test_schema_cdeps_streams(cdeps_config, section):
    block = cdeps_config[f"{section}_streams"]
    errors = schema_validator("cdeps", "properties", "cdeps", "properties", f"{section}_streams")
    # Both top-level keys are required:
    for k in ["streams", "template_file"]:
        assert f"'{k}' is a required property" in errors(with_del(block, k))
    # Correctly-named stream blocks are ok:
    for n in range(1, 10):
        assert not errors(with_set(block, block["streams"]["stream01"], "streams", f"stream0{n}"))
    # Arbitrarily-named stream blocks are not allowed:
    assert "does not match any of the regexes" in errors(with_set(block, {}, "streams", "foo"))
    # template_file must be a string:
    assert "is not of type 'string'\n" in errors(with_set(block, 1, "template_file"))
    # Values must be of the correct types:
    valerr = lambda k, v: errors(with_set(block, v, "streams", "stream01", k))
    # enum:
    ks_enum = ["readmode"]
    assert "is not one of" in valerr("readmode", None)
    # integer:
    ks_integer = ["stream_offset", "yearAlign", "yearFirst", "yearLast"]
    for k in ks_integer:
        assert "is not of type 'integer'\n" in valerr(k, None)
    # number:
    ks_number = ["dtlimit"]
    for k in ks_number:
        assert "is not of type 'number'\n" in valerr(k, None)
    # string:
    ks_string = ["mapalgo", "stream_lev_dimname", "stream_mesh_file", "taxmode", "tinterpalgo"]
    for k in ks_string:
        assert "is not of type 'string'\n" in valerr(k, None)
    # string arrays:
    ks_string_array = ["stream_data_files", "stream_data_variables"]
    for k in ks_string_array:
        assert "is not of type 'array'\n" in valerr(k, None)
        assert "is not of type 'string'\n" in valerr(k, [1])
    # string or string array:
    ks_string_or_string_array = ["stream_vectors"]
    for k in ks_string_or_string_array:
        assert "is not of type 'array', 'string'\n" in valerr(k, None)
        assert "is not of type 'string'\n" in valerr(k, [1])
    # All keys are required:
    for k in ks_enum + ks_integer + ks_number + ks_string + ks_string_array:
        assert "is a required property" in errors(with_del(block, "streams", "stream01", k))


# chgres-cube


def test_schema_chgres_cube(chgres_cube_config):
    errors = schema_validator("chgres-cube", "properties", "chgres_cube")
    # Basic correctness:
    assert not errors(chgres_cube_config)
    # Some top-level keys are required:
    for key in ("execution", "namelist", "rundir"):
        assert f"'{key}' is a required property" in errors(with_del(chgres_cube_config, key))
    # Additional top-level keys are not allowed:
    assert "Additional properties are not allowed" in errors({**chgres_cube_config, "foo": "bar"})
    # "rundir" must be present, and must be a string:
    assert "'rundir' is a required property" in errors(with_del(chgres_cube_config, "rundir"))
    assert "is not of type 'string'\n" in errors(with_set(chgres_cube_config, None, "rundir"))


def test_schema_chgres_cube_namelist(chgres_cube_config, chgres_cube_prop):
    namelist = chgres_cube_config["namelist"]
    errors = chgres_cube_prop("namelist")
    # Just base_file is ok:
    assert not errors(with_del(namelist, "update_values"))
    # base_file must be a string:
    assert "42 is not of type 'string'\n" in errors(with_set(namelist, 42, "base_file"))
    # Just update_values is ok:
    assert not errors(with_del(namelist, "base_file"))
    # config is required with update_values:
    assert "'config' is a required property" in errors(
        with_del(namelist, "update_values", "config")
    )
    # At least one is required:
    assert "is not valid" in errors({})


def test_schema_chgres_cube_namelist_update_values(chgres_cube_config, chgres_cube_prop):
    config = chgres_cube_config["namelist"]["update_values"]["config"]
    errors = chgres_cube_prop("namelist", "properties", "update_values", "properties", "config")
    # Some entries are required:
    for key in ["mosaic_file_target_grid", "vcoord_file_target_grid"]:
        assert "is a required property" in errors(with_del(config, key))
    # Additional entries of namelist-compatible types are permitted:
    for val in [[1, 2, 3], True, 42, 3.14, "bar"]:
        assert not errors(with_set(config, val, "foo"))
    # Namelist values must be of the correct type:
    # boolean:
    for key in [
        "convert_atm",
        "convert_nst",
        "convert_sfc",
        "lai_from_climo",
        "minmax_vgfrc_from_climo",
        "sotyp_from_climo",
        "tg3_from_soil",
        "vgfrc_from_climo",
        "vgtyp_from_climo",
        "wam_cold_start",
    ]:
        assert "not of type 'boolean'" in errors(with_set(config, None, key))
    # enum:
    for key in ["external_model", "input_type"]:
        assert "is not one of" in errors(with_set(config, None, key))
    # integer:
    for key in [
        "cycle_day",
        "cycle_hour",
        "cycle_mon",
        "cycle_year",
        "halo_blend",
        "halo_bndy",
        "nsoill_out",
        "regional",
    ]:
        assert "not of type 'integer'" in errors(with_set(config, None, key))
    # string:
    for key in [
        "atm_weight_file",
        "data_dir_input_grid",
        "fix_dir_target_grid",
        "geogrid_file_input_grid",
        "grib2_file_input_grid",
        "mosaic_file_input_grid",
        "mosaic_file_target_grid",
        "orog_dir_input_grid",
        "orog_dir_target_grid",
        "thomp_mp_climo_file",
        "varmap_file",
        "varmap_file",
        "vcoord_file_target_grid",
        "wam_parm_file",
    ]:
        assert "not of type 'string'" in errors(with_set(config, None, key))
    # string or array of string:
    for key in [
        "atm_core_files_input_grid",
        "atm_files_input_grid",
        "atm_tracer_files_input_grid",
        "nst_files_input_grid",
        "orog_files_input_grid",
        "orog_files_target_grid",
        "sfc_files_input_grid",
    ]:
        assert "is not of type 'array', 'string'\n" in errors(with_set(config, None, key))
        assert "is not of type 'string'\n" in errors(with_set(config, [1, 2, 3], key))


# esg-grid


def test_schema_esg_grid():
    config = {
        "execution": {"executable": "esg_grid"},
        "namelist": {"base_file": "/path", "validate": True},
        "rundir": "/tmp",
    }
    errors = schema_validator("esg-grid", "properties", "esg_grid")
    # Basic correctness:
    assert not errors(config)
    # Some top-level keys are required:
    for key in ("execution", "namelist", "rundir"):
        assert f"'{key}' is a required property" in errors(with_del(config, key))
    # Additional top-level keys are not allowed:
    assert "Additional properties are not allowed" in errors({**config, "foo": "bar"})
    # Additional MPI support is not allowed:
    assert "Additional properties are not allowed ('mpicmd' was unexpected)" in errors(
        {"execution": {"mpicmd": "srun"}}
    )


def test_schema_esg_grid_namelist(esg_grid_prop, esg_namelist):
    errors = esg_grid_prop("namelist")
    # Just base_file is ok:
    assert not errors(esg_namelist)
    # base_file must be a string:
    assert "not valid" in errors({**esg_namelist, "base_file": 42})
    # Just update_values is ok, if it is complete:
    assert not errors(with_del(esg_namelist, "base_file"))
    # If base_file is not supplied, any missing namelist key is an error:
    assert "not valid" in errors(
        with_del(with_del(esg_namelist, "update_values", "regional_grid_nml", "delx"), "base_file")
    )
    # A missing namelist key is ok if base_file is supplied:
    assert not errors(with_del(esg_namelist, "update_values", "regional_grid_nml", "delx"))
    # regional_grid_nml is required with update_values:
    assert "not valid" in errors(with_del(esg_namelist, "update_values", "regional_grid_nml"))
    # At least one of base_file and/or update_values is required:
    assert "not valid" in errors({})


@mark.parametrize("key", ["delx", "dely", "lx", "ly", "pazi", "plat", "plon"])
def test_schema_esg_grid_namelist_content(key):
    config: dict = {
        "regional_grid_nml": {
            "delx": 42,
            "dely": 42,
            "lx": 42,
            "ly": 42,
            "pazi": 42,
            "plat": 42,
            "plon": 42,
        }
    }
    errors = partial(schema_validator("esg-grid", "$defs", "namelist_content"))
    assert not errors(config)
    # A floating-point value is ok:
    config["regional_grid_nml"][key] = 3.14
    assert not errors(config)
    # It is an error for the value to be of type string:
    config["regional_grid_nml"][key] = "foo"
    assert "not of type 'number'" in errors(config)
    # Each key is required:
    assert "is a required property" in errors(with_del(config, "regional_grid_nml", key))


def test_schema_esg_grid_rundir(esg_grid_prop):
    errors = esg_grid_prop("rundir")
    # Must be a string:
    assert not errors("/some/path")
    assert "42 is not of type 'string'\n" in errors(42)


# execution


def test_schema_execution():
    config = {"executable": "fv3"}
    batchargs = {"batchargs": {"queue": "string", "walltime": "string"}}
    mpiargs = {"mpiargs": ["--flag1", "--flag2"]}
    threads = {"threads": 32}
    errors = schema_validator("execution")
    # Basic correctness:
    assert not errors(config)
    # batchargs may optionally be specified:
    assert not errors({**config, **batchargs})
    # mpiargs may be optionally specified:
    assert not errors({**config, **mpiargs})
    # threads may optionally be specified:
    assert not errors({**config, **threads})
    # All properties are ok:
    assert not errors({**config, **batchargs, **mpiargs, **threads})
    # Additional properties are not allowed:
    assert "Additional properties are not allowed" in errors(
        {**config, **mpiargs, **threads, "foo": "bar"}
    )


def test_schema_execution_executable():
    errors = schema_validator("execution", "properties", "executable")
    # String value is ok:
    assert not errors("fv3.exe")
    # Anything else is not:
    assert "42 is not of type 'string'\n" in errors(42)


def test_schema_execution_mpiargs():
    errors = schema_validator("execution", "properties", "mpiargs")
    # Basic correctness:
    assert not errors(["string1", "string2"])
    # mpiargs may be empty:
    assert not errors([])
    # String values are expected:
    assert "42 is not of type 'string'\n" in errors(["string1", 42])


def test_schema_execution_threads():
    errors = schema_validator("execution", "properties", "threads")
    # threads must be non-negative, and an integer:
    assert not errors(1)
    assert not errors(4)
    assert "0 is less than the minimum of 1" in errors(0)
    assert "3.14 is not of type 'integer'\n" in errors(3.14)


# execution-serial


def test_schema_execution_serial():
    config = {"executable": "fv3"}
    batchargs = {"batchargs": {"queue": "string", "walltime": "string"}}
    errors = schema_validator("execution")
    # Basic correctness:
    assert not errors(config)
    # batchargs may optionally be specified:
    assert not errors({**config, **batchargs})
    # All properties are ok:
    assert not errors({**config, **batchargs})
    # Additional properties are not allowed:
    assert "Additional properties are not allowed" in errors({**config, "foo": "bar"})


# files-to-stage


def test_schema_stage_files():
    errors = schema_validator("files-to-stage")
    # The input must be an dict:
    assert "is not of type 'object'\n" in errors([])
    # A str -> str dict is ok:
    assert not errors({"file1": "/path/to/file1", "file2": "/path/to/file2"})
    # An empty dict is not allowed:
    assert "{} should be non-empty" in errors({})
    # Non-string values are not allowed:
    assert "True is not of type 'string'\n" in errors({"file1": True})


# filter-topo


def test_schema_filter_topo():
    config = {
        "config": {
            "input_grid_file": "/path/to/grid/file",
            "filtered_orog": "/path/to/filtered/orog/file",
            "input_raw_orog": "/path/to/raw/orog/file",
        },
        "execution": {
            "executable": "/path/to/filter_topo",
        },
        "namelist": {
            "update_values": {
                "filter_topo_nml": {
                    "grid_file": "/path/to/grid/file",
                    "grid_type": 0,
                    "mask_field": "land_frac",
                    "regional": True,
                    "res": 403,
                    "stretch_fac": 0.999,
                    "topo_field": "orog_filt",
                    "topo_file": "/path/to/topo/file",
                    "zero_ocean": True,
                }
            }
        },
        "rundir": "/path/to/run/dir",
    }
    errors = schema_validator("filter-topo", "properties", "filter_topo")
    nmlkeys = ("namelist", "update_values", "filter_topo_nml")
    # Basic correctness:
    assert not errors(config)
    # All top-level keys are requried:
    for key in ["config", "execution", "namelist", "rundir"]:
        assert f"'{key}' is a required property" in errors(with_del(config, key))
    # Other top-level keys are not allowed:
    assert "Additional properties are not allowed" in errors(with_set(config, "bar", "foo"))
    # Top-level rundir key requires a string value:
    assert "is not of type 'string'\n" in errors(with_set(config, None, "rundir"))
    # All config keys are requried:
    for key in ["filtered_orog", "input_grid_file", "input_raw_orog"]:
        assert f"'{key}' is a required property" in errors(with_del(config, "config", key))
    # Other config keys are not allowed:
    assert "Additional properties are not allowed" in errors(
        with_set(config, "bar", "config", "foo")
    )
    # Some config keys require string values:
    for key in ["input_grid_file"]:
        assert "is not of type 'string'\n" in errors(with_set(config, None, "config", key))
    # Namelist filter_topo_nml is required:
    assert "is a required property" in errors(with_del(config, *nmlkeys))
    # Additional namelists are not allowed:
    assert "not allowed" in errors(
        with_set(config, {}, "namelist", "update_values", "additonal_namelist")
    )
    # All filter_topo_nml keys are optional:
    for key in [
        "grid_file",
        "grid_type",
        "mask_field",
        "regional",
        "res",
        "stretch_fac",
        "topo_field",
        "topo_file",
        "zero_ocean",
    ]:
        assert not errors(with_del(config, *nmlkeys, key))
    # Additional filter_topo_nml keys are allowd:
    assert not errors(with_set(config, "val", *nmlkeys, "key"))
    # Some filter_topo_nml keys require boolean values:
    for key in ["regional", "zero_ocean"]:
        assert "is not of type 'boolean'\n" in errors(with_set(config, None, *nmlkeys, key))
    # Some filter_topo_nml keys require integer values:
    for key in ["grid_type", "res"]:
        assert "is not of type 'integer'\n" in errors(with_set(config, None, *nmlkeys, key))
    # Some filter_topo_nml keys require number values:
    for key in ["stretch_fac"]:
        assert "is not of type 'number'\n" in errors(with_set(config, None, *nmlkeys, key))
    # Some filter_topo_nml keys require string values:
    for key in ["grid_file", "mask_field", "topo_field", "topo_file"]:
        assert "is not of type 'string'\n" in errors(with_set(config, None, *nmlkeys, key))


# fv3


def test_schema_fv3():
    config = {
        "domain": "regional",
        "execution": {"executable": "fv3"},
        "field_table": {"base_file": "/path"},
        "lateral_boundary_conditions": {"interval_hours": 1, "offset": 0, "path": "/tmp/file"},
        "length": 3,
        "namelist": {"base_file": "/path", "validate": True},
        "rundir": "/tmp",
    }
    errors = schema_validator("fv3", "properties", "fv3")
    # Basic correctness:
    assert not errors(config)
    # Some top-level keys are required:
    for key in (
        "domain",
        "execution",
        "lateral_boundary_conditions",
        "length",
        "namelist",
        "rundir",
    ):
        assert f"'{key}' is a required property" in errors(with_del(config, key))
    # Some top-level keys are optional:
    assert not errors(
        {
            **config,
            "diag_table": "/path",
            "files_to_copy": {"fn": "/path"},
            "files_to_link": {"fn": "/path"},
            "model_configure": {"base_file": "/path"},
            "namelist": {"base_file": "/path", "validate": True},
        }
    )
    # Additional top-level keys are not allowed:
    assert "Additional properties are not allowed" in errors({**config, "foo": "bar"})
    # lateral_boundary_conditions are optional when domain is global:
    assert not errors({**with_del(config, "lateral_boundary_conditions"), "domain": "global"})


def test_schema_fv3_diag_table(fv3_prop):
    errors = fv3_prop("diag_table")
    # String value is ok:
    assert not errors("/path/to/file")
    # Anything else is not:
    assert "42 is not of type 'string'\n" in errors(42)


def test_schema_fv3_domain(fv3_prop):
    errors = fv3_prop("domain")
    # There is a fixed set of domain values:
    assert "'foo' is not one of ['global', 'regional']" in errors("foo")


def test_schema_fv3_lateral_boundary_conditions(fv3_prop):
    config = {
        "interval_hours": 1,
        "offset": 0,
        "path": "/some/path",
    }
    errors = fv3_prop("lateral_boundary_conditions")
    # Basic correctness:
    assert not errors(config)
    # All lateral_boundary_conditions items are required:
    assert "'interval_hours' is a required property" in errors(with_del(config, "interval_hours"))
    assert "'offset' is a required property" in errors(with_del(config, "offset"))
    assert "'path' is a required property" in errors(with_del(config, "path"))
    # interval_hours must be an integer of at least 1:
    assert "0 is less than the minimum of 1" in errors(with_set(config, 0, "interval_hours"))
    assert "'s' is not of type 'integer'\n" in errors(with_set(config, "s", "interval_hours"))
    # offset must be an integer of at least 0:
    assert "-1 is less than the minimum of 0" in errors(with_set(config, -1, "offset"))
    assert "'s' is not of type 'integer'\n" in errors(with_set(config, "s", "offset"))
    # path must be a string:
    assert "42 is not of type 'string'\n" in errors(with_set(config, 42, "path"))


def test_schema_fv3_length(fv3_prop):
    errors = fv3_prop("length")
    # Positive int is ok:
    assert not errors(6)
    # Zero is not ok:
    assert "0 is less than the minimum of 1" in errors(0)
    # A negative number is not ok:
    assert "-1 is less than the minimum of 1" in errors(-1)
    # Something other than an int is not ok:
    assert "'a string' is not of type 'integer'\n" in errors("a string")


def test_schema_fv3_model_configure(fv3_prop):
    base_file = {"base_file": "/some/path"}
    update_values = {"update_values": {"foo": 42}}
    errors = fv3_prop("model_configure")
    # Just base_file is ok:
    assert not errors(base_file)
    # But base_file must be a string:
    assert "42 is not of type 'string'\n" in errors({"base_file": 42})
    # Just update_values is ok:
    assert not errors(update_values)
    # A combination of base_file and update_values is ok:
    assert not errors({**base_file, **update_values})
    # At least one is required:
    assert "is not valid" in errors({})


def test_schema_fv3_model_configure_update_values(fv3_prop):
    errors = fv3_prop("model_configure", "properties", "update_values")
    # boolean, number, and string values are ok:
    assert not errors({"bool": True, "int": 42, "float": 3.14, "string": "foo"})
    # Other types are not, e.g.:
    assert "None is not of type 'boolean', 'number', 'string'\n" in errors({"null": None})
    # At least one entry is required:
    assert "{} should be non-empty" in errors({})


def test_schema_fv3_namelist(fv3_prop):
    base_file = {"base_file": "/some/path"}
    update_values = {"update_values": {"nml": {"var": "val"}}}
    errors = fv3_prop("namelist")
    # Just base_file is ok:
    assert not errors(base_file)
    # base_file must be a string:
    assert "42 is not of type 'string'\n" in errors({"base_file": 42})
    # Just update_values is ok:
    assert not errors(update_values)
    # A combination of base_file and update_values is ok:
    assert not errors({**base_file, **update_values})
    # At least one is required:
    assert "is not valid" in errors({})


def test_schema_fv3_namelist_update_values(fv3_prop):
    errors = fv3_prop("namelist", "properties", "update_values")
    # array, boolean, number, and string values are ok:
    assert not errors(
        {"nml": {"array": [1, 2, 3], "bool": True, "int": 42, "float": 3.14, "string": "foo"}}
    )
    # Other types are not, e.g.:
    assert "None is not of type 'array', 'boolean', 'number', 'string'\n" in errors(
        {"nml": {"null": None}}
    )
    # At least one namelist entry is required:
    assert "{} should be non-empty" in errors({})
    # At least one val/var pair is required:
    assert "{} should be non-empty" in errors({"nml": {}})


def test_schema_fv3_rundir(fv3_prop):
    errors = fv3_prop("rundir")
    # Must be a string:
    assert not errors("/some/path")
    assert "42 is not of type 'string'\n" in errors(42)


# global-equiv-resol


def test_schema_global_equiv_resol():
    config = {
        "execution": {"executable": "/tmp/global_equiv_resol.exe"},
        "input_grid_file": "/tmp/input_grid_file",
        "rundir": "/tmp",
    }
    errors = schema_validator("global-equiv-resol", "properties", "global_equiv_resol")
    # Basic correctness:
    assert not errors(config)
    # All top-level keys are required:
    for key in ("execution", "input_grid_file", "rundir"):
        assert f"'{key}' is a required property" in errors(with_del(config, key))
    # Additional top-level keys are not allowed:
    assert "Additional properties are not allowed" in errors({**config, "foo": "bar"})


@mark.parametrize("schema_entry", ["rundir", "input_grid_file"])
def test_schema_global_equiv_resol_paths(global_equiv_resol_prop, schema_entry):
    errors = global_equiv_resol_prop(schema_entry)
    # Must be a string:
    assert not errors("/some/path")
    assert "42 is not of type 'string'\n" in errors(42)


# ioda


def test_schema_ioda():
    config = {
        "configuration_file": {
            "base_file": "/path/to/ioda.yaml",
            "update_values": {"foo": "bar", "baz": "qux"},
        },
        "execution": {"executable": "/tmp/ioda.exe"},
        "files_to_copy": {"file1": "src1", "file2": "src2"},
        "files_to_link": {"link1": "src3", "link2": "src4"},
        "rundir": "/tmp",
    }
    errors = schema_validator("ioda", "properties", "ioda")
    # Basic correctness:
    assert not errors(config)
    # All top-level keys are required:
    for key in ("configuration_file", "execution", "rundir"):
        assert f"'{key}' is a required property" in errors(with_del(config, key))
    # Additional top-level keys are not allowed:
    assert "Additional properties are not allowed" in errors({**config, "foo": "bar"})


def test_schema_ioda_configuration_file(ioda_prop):
    bf = {"base_file": "/path/to/ioda.yaml"}
    uv = {"update_values": {"foo": "bar", "baz": "qux"}}
    errors = ioda_prop("configuration_file")
    # base_file and update_values are ok together:
    assert not errors({**bf, **uv})
    # And either is ok alone:
    assert not errors(bf)
    assert not errors(uv)
    # update_values cannot be empty:
    assert "should be non-empty" in errors({"update_values": {}})


def test_schema_ioda_rundir(ioda_prop):
    errors = ioda_prop("rundir")
    # Must be a string:
    assert not errors("/some/path")
    assert "42 is not of type 'string'\n" in errors(42)


# jedi


def test_schema_jedi():
    config = {
        "configuration_file": {
            "base_file": "/path/to/jedi.yaml",
            "update_values": {"foo": "bar", "baz": "qux"},
        },
        "execution": {"executable": "/tmp/jedi.exe"},
        "files_to_copy": {"file1": "src1", "file2": "src2"},
        "files_to_link": {"link1": "src3", "link2": "src4"},
        "rundir": "/tmp",
    }
    errors = schema_validator("jedi", "properties", "jedi")
    # Basic correctness:
    assert not errors(config)
    # All top-level keys are required:
    for key in ("configuration_file", "execution", "rundir"):
        assert f"'{key}' is a required property" in errors(with_del(config, key))
    # Additional top-level keys are not allowed:
    assert "Additional properties are not allowed" in errors({**config, "foo": "bar"})


def test_schema_jedi_configuration_file(jedi_prop):
    bf = {"base_file": "/path/to/jedi.yaml"}
    uv = {"update_values": {"foo": "bar", "baz": "qux"}}
    errors = jedi_prop("configuration_file")
    # base_file and update_values are ok together:
    assert not errors({**bf, **uv})
    # And either is ok alone:
    assert not errors(bf)
    assert not errors(uv)
    # update_values cannot be empty:
    assert "should be non-empty" in errors({"update_values": {}})


def test_schema_jedi_rundir(jedi_prop):
    errors = jedi_prop("rundir")
    # Must be a string:
    assert not errors("/some/path")
    assert "42 is not of type 'string'\n" in errors(42)


# make-hgrid


def test_schema_make_hgrid():
    config = {
        "config": {"grid_type": "from_file", "my_grid_file": "/path/to/my_grid_file"},
        "execution": {"executable": "make_hgrid"},
        "rundir": "/tmp",
    }
    errors = schema_validator("make-hgrid", "properties", "make_hgrid")
    # Basic correctness:
    assert not errors(config)
    # All top-level keys are required:
    for key in ("config", "execution", "rundir"):
        assert f"'{key}' is a required property" in errors(with_del(config, key))
    # Additional top-level keys are not allowed:
    assert "Additional properties are not allowed" in errors({**config, "foo": "bar"})


def test_schema_make_hgrid_grid_type():
    # Get errors function from schema_validator
    errors = schema_validator("make-hgrid", "properties", "make_hgrid", "properties", "config")

    # config needs at least the grid_type key:
    assert "'grid_type' is a required property" in errors({})

    # If grid_type is "from_file", my_grid_file is required
    assert "'my_grid_file' is a required property" in errors({"grid_type": "from_file"})

    # If grid_type is "tripolar_grid" or "regular_lonlat_grid",
    # nxbnds, nybnds, xbnds, and ybnds are required.
    for prop in ("nxbnds", "nybnds", "xbnds", "ybnds"):
        for grid_type in ("tripolar_grid", "regular_lonlat_grid"):
            assert f"'{prop}' is a required property" in errors({"grid_type": grid_type})

    # If grid_type is "simple_cartesian_grid",
    # nxbnds, nybnds, xbnds, ybnds, simple_dx, and simple_dy are required
    for prop in ("nxbnds", "nybnds", "xbnds", "ybnds", "simple_dx", "simple_dy"):
        assert f"'{prop}' is a required property" in errors({"grid_type": "simple_cartesian_grid"})

    # If grid_type is "f_plane_grid" or "beta_plane_grid", f_plane_latitude is required.
    for grid_type in ("f_plane_grid", "beta_plane_grid"):
        assert "'f_plane_latitude' is a required property" in errors({"grid_type": grid_type})

    # If grid_type is "gnomonic_ed" and nest_grids is present, halo is required
    assert "'halo' is a required property" in errors({"grid_type": "gnomonic_ed", "nest_grids": 1})

    # If do_schmidt and do_cube_transform are present,
    # stretch_factor, target_lat, and target_lon are required
    for prop in ("stretch_factor", "target_lat", "target_lon"):
        assert f"'{prop}' is a required property" in errors(
            {"do_schmidt": True, "do_cube_transform": True}
        )


def test_schema_make_hgrid_rundir(make_hgrid_prop):
    errors = make_hgrid_prop("rundir")
    # Must be a string:
    assert not errors("/some/path")
    assert "42 is not of type 'string'\n" in errors(42)


# make-solo-mosaic


def test_schema_make_solo_mosaic():
    config = {
        "config": {"dir": "path/to/dir", "num_tiles": 1},
        "execution": {"executable": "make_solo_mosaic"},
        "rundir": "/tmp",
    }
    errors = schema_validator("make-solo-mosaic", "properties", "make_solo_mosaic")
    # Basic correctness:
    assert not errors(config)
    # All top-level keys are required:
    for key in ("config", "execution", "rundir"):
        assert f"'{key}' is a required property" in errors(with_del(config, key))
    # Additional top-level keys are not allowed:
    assert "Additional properties are not allowed" in errors({**config, "foo": "bar"})


def test_schema_make_solo_mosaic_config(make_solo_mosaic_prop):
    errors = make_solo_mosaic_prop("config")
    for key in ("dir", "num_tiles"):
        # All config keys are required:
        assert f"'{key}' is a required property" in errors({})
        # A string value is ok for dir:
        if key == "dir":
            assert "not of type 'string'" in str(errors({key: 42}))
        # num_tiles must be an integer:
        else:
            assert "not of type 'integer'" in str(errors({key: "/path/"}))
        # It is an error for the value to be a floating-point value:
        assert "not of type" in str(errors({key: 3.14}))
        # It is an error not to supply a value:
        assert "None is not of type" in str(errors({key: None}))


def test_schema_make_solo_mosaic_rundir(make_solo_mosaic_prop):
    errors = make_solo_mosaic_prop("rundir")
    # Must be a string:
    assert not errors("/some/path")
    assert "42 is not of type 'string'\n" in errors(42)


# makedirs


def test_schema_makedirs():
    errors = schema_validator("makedirs")
    # The input must be an dict:
    assert "is not of type 'object'\n" in errors([])
    # Basic correctness:
    assert not errors({"makedirs": ["/path/to/dir1", "/path/to/dir2"]})
    # An empty array is not allowed:
    assert "[] should be non-empty" in errors({"makedirs": []})
    # Non-string values are not allowed:
    assert "True is not of type 'string'\n" in errors({"makedirs": [True]})


# mpas


def test_schema_mpas(mpas_streams):
    config = {
        "execution": {"executable": "atmosphere_model"},
        "namelist": {"base_file": "path/to/simple.nml", "validate": True},
        "rundir": "path/to/rundir",
        "streams": mpas_streams,
    }
    errors = schema_validator("mpas", "properties", "mpas")
    # Basic correctness:
    assert not errors(config)
    # All top-level keys are required:
    for key in ("execution", "namelist", "rundir", "streams"):
        assert f"'{key}' is a required property" in errors(with_del(config, key))
    # Additional top-level keys are not allowed:
    assert "Additional properties are not allowed" in errors({**config, "foo": "bar"})


def test_schema_mpas_lateral_boundary_conditions(mpas_prop):
    config = {
        "interval_hours": 1,
        "offset": 0,
        "path": "/some/path",
    }
    errors = mpas_prop("lateral_boundary_conditions")
    # Basic correctness:
    assert not errors(config)
    # All lateral_boundary_conditions items are required:
    assert "'interval_hours' is a required property" in errors(with_del(config, "interval_hours"))
    assert "'offset' is a required property" in errors(with_del(config, "offset"))
    assert "'path' is a required property" in errors(with_del(config, "path"))
    # interval_hours must be an integer of at least 1:
    assert "0 is less than the minimum of 1" in errors(with_set(config, 0, "interval_hours"))
    assert "'s' is not of type 'integer'\n" in errors(with_set(config, "s", "interval_hours"))
    # offset must be an integer of at least 0:
    assert "-1 is less than the minimum of 0" in errors(with_set(config, -1, "offset"))
    assert "'s' is not of type 'integer'\n" in errors(with_set(config, "s", "offset"))
    # path must be a string:
    assert "42 is not of type 'string'\n" in errors(with_set(config, 42, "path"))


def test_schema_mpas_length(mpas_prop):
    errors = mpas_prop("length")
    # Positive int is ok:
    assert not errors(6)
    # Zero is not ok:
    assert "0 is less than the minimum of 1" in errors(0)
    # A negative number is not ok:
    assert "-1 is less than the minimum of 1" in errors(-1)
    # Something other than an int is not ok:
    assert "'a string' is not of type 'integer'\n" in errors("a string")


def test_schema_mpas_namelist(mpas_prop):
    base_file = {"base_file": "/some/path"}
    update_values = {"update_values": {"nml": {"var": "val"}}}
    errors = mpas_prop("namelist")
    # Just base_file is ok:
    assert not errors(base_file)
    # base_file must be a string:
    assert "42 is not of type 'string'\n" in errors({"base_file": 42})
    # Just update_values is ok:
    assert not errors(update_values)
    # A combination of base_file and update_values is ok:
    assert not errors({**base_file, **update_values})
    # At least one is required:
    assert "is not valid" in errors({})


def test_schema_mpas_namelist_update_values(mpas_prop):
    errors = mpas_prop("namelist", "properties", "update_values")
    # array, boolean, number, and string values are ok:
    assert not errors(
        {"nml": {"array": [1, 2, 3], "bool": True, "int": 42, "float": 3.14, "string": "foo"}}
    )
    # Other types are not, e.g.:
    assert "None is not of type 'array', 'boolean', 'number', 'string'\n" in errors(
        {"nml": {"null": None}}
    )
    # At least one namelist entry is required:
    assert "{} should be non-empty" in errors({})
    # At least one val/var pair is required:
    assert "{} should be non-empty" in errors({"nml": {}})


def test_schema_mpas_rundir(mpas_prop):
    errors = mpas_prop("rundir")
    # Must be a string:
    assert not errors("/some/path")
    assert "42 is not of type 'string'\n" in errors(42)


# mpas-init


def test_schema_mpas_init(mpas_streams):
    config = {
        "execution": {"executable": "mpas_init"},
        "namelist": {"base_file": "path/to/simple.nml", "validate": True},
        "rundir": "path/to/rundir",
        "streams": mpas_streams,
    }
    errors = schema_validator("mpas-init", "properties", "mpas_init")
    # Basic correctness:
    assert not errors(config)
    # All top-level keys are required:
    for key in ("execution", "namelist", "rundir", "streams"):
        assert f"'{key}' is a required property" in errors(with_del(config, key))
    # Additional top-level keys are not allowed:
    assert "Additional properties are not allowed" in errors({**config, "foo": "bar"})


def test_schema_mpas_init_boundary_conditions(mpas_init_prop):
    config = {
        "interval_hours": 1,
        "length": 1,
        "offset": 0,
        "path": "/some/path",
    }
    errors = mpas_init_prop("boundary_conditions")
    # Basic correctness:
    assert not errors(config)
    # All lateral_boundary_conditions items are required:
    assert "'interval_hours' is a required property" in errors(with_del(config, "interval_hours"))
    assert "'length' is a required property" in errors(with_del(config, "length"))
    assert "'offset' is a required property" in errors(with_del(config, "offset"))
    assert "'path' is a required property" in errors(with_del(config, "path"))
    # interval_hours must be an integer of at least 1:
    assert "0 is less than the minimum of 1" in errors(with_set(config, 0, "interval_hours"))
    assert "'s' is not of type 'integer'\n" in errors(with_set(config, "s", "interval_hours"))
    # offset must be an integer of at least 0:
    assert "-1 is less than the minimum of 0" in errors(with_set(config, -1, "offset"))
    assert "'s' is not of type 'integer'\n" in errors(with_set(config, "s", "offset"))
    # path must be a string:
    assert "42 is not of type 'string'\n" in errors(with_set(config, 42, "path"))
    # length must be a positive int
    assert "0 is less than the minimum of 1" in errors(with_set(config, 0, "length"))
    assert "-1 is less than the minimum of 1" in errors(with_set(config, -1, "length"))
    assert "'s' is not of type 'integer'\n" in errors(with_set(config, "s", "length"))


def test_schema_mpas_init_namelist(mpas_init_prop):
    base_file = {"base_file": "/some/path"}
    update_values = {"update_values": {"nml": {"var": "val"}}}
    errors = mpas_init_prop("namelist")
    # Just base_file is ok:
    assert not errors(base_file)
    # base_file must be a string:
    assert "42 is not of type 'string'\n" in errors({"base_file": 42})
    # Just update_values is ok:
    assert not errors(update_values)
    # A combination of base_file and update_values is ok:
    assert not errors({**base_file, **update_values})
    # At least one is required:
    assert "is not valid" in errors({})


def test_schema_mpas_init_namelist_update_values(mpas_init_prop):
    errors = mpas_init_prop("namelist", "properties", "update_values")
    # array, boolean, number, and string values are ok:
    assert not errors(
        {"nml": {"array": [1, 2, 3], "bool": True, "int": 42, "float": 3.14, "string": "foo"}}
    )
    # Other types are not, e.g.:
    assert "None is not of type 'array', 'boolean', 'number', 'string'\n" in errors(
        {"nml": {"null": None}}
    )
    # At least one namelist entry is required:
    assert "{} should be non-empty" in errors({})
    # At least one val/var pair is required:
    assert "{} should be non-empty" in errors({"nml": {}})


def test_schema_mpas_init_rundir(mpas_init_prop):
    errors = mpas_init_prop("rundir")
    # Must be a string:
    assert not errors("/some/path")
    assert "42 is not of type 'string'\n" in errors(42)


# mpas-streams


def test_schema_mpas_streams(mpas_streams):
    errors = schema_validator("mpas-streams")
    # Basic correctness:
    assert not errors(mpas_streams)


def test_schema_mpas_streams_intervals(mpas_streams):
    # Interval items are conditionally required based on input/output settings.
    errors = schema_validator("mpas-streams")
    assert "'input_interval' is a required property" in errors(
        with_del(mpas_streams, "input", "input_interval")
    )
    assert "'output_interval' is a required property" in errors(
        with_del(mpas_streams, "output", "output_interval")
    )
    x = {"x": {"filename_template": "t", "mutable": False, "type": "input;output"}}
    assert "'input_interval' is a required property" in errors(
        {**x, "output_interval": "initial_only"}
    )
    assert "'output_interval' is a required property" in errors(
        {**x, "input_interval": "initial_only"}
    )


def test_schema_mpas_streams_properties_optional(mpas_streams):
    props = {
        "clobber_mode",
        "filename_interval",
        "files",
        "io_type",
        "packages",
        "precision",
        "reference_time",
        "streams",
        "var_arrays",
        "var_structs",
        "vars",
    }
    exercised = set()
    errors = schema_validator("mpas-streams")
    for k, v in mpas_streams.items():
        for prop in props:
            if prop in v:
                assert not errors(with_del(mpas_streams, k, prop))
                exercised.add(prop)
    assert exercised == props


def test_schema_mpas_streams_properties_required(mpas_streams):
    props = {"filename_template", "mutable", "type"}
    exercised = set()
    errors = schema_validator("mpas-streams")
    for k, v in mpas_streams.items():
        for prop in props:
            if prop in v:
                assert "is a required property" in errors(with_del(mpas_streams, k, prop))
                exercised.add(prop)
    assert exercised == props


def test_schema_mpas_streams_properties_values_array(mpas_streams):
    errors = schema_validator("mpas-streams")
    for k, v in mpas_streams.items():
        for prop in ["files", "streams", "vars", "var_arrays", "var_structs"]:
            assert "is not of type 'array'\n" in errors({k: {**v, prop: None}})
            assert "is not of type 'string'\n" in errors({k: {**v, prop: [None]}})
            assert "should be non-empty" in errors({k: {**v, prop: []}})


def test_schema_mpas_streams_properties_boolean(mpas_streams):
    errors = schema_validator("mpas-streams")
    for k, v in mpas_streams.items():
        for prop in ["mutable"]:
            assert "is not of type 'boolean'\n" in errors({k: {**v, prop: None}})


def test_schema_mpas_streams_properties_enum(mpas_streams):
    errors = schema_validator("mpas-streams")
    for k, v in mpas_streams.items():
        assert (
            "is not one of ['overwrite', 'truncate', 'replace_files', 'never_modify', 'append']"
            in errors({k: {**v, "clobber_mode": None}})
        )
        assert "is not one of ['pnetcdf', 'pnetcdf,cdf5', 'netcdf', 'netcdf4']" in errors(
            {k: {**v, "io_type": None}}
        )
        assert "is not one of ['single', 'double', 'native']" in errors(
            {k: {**v, "precision": None}}
        )
        assert "is not one of ['input', 'input;output', 'none', 'output'" in errors(
            {k: {**v, "type": None}}
        )


def test_schema_mpas_streams_properties_string(mpas_streams):
    errors = schema_validator("mpas-streams")
    for k, v in mpas_streams.items():
        for prop in [
            "filename_interval",
            "filename_template",
            "input_interval",
            "output_interval",
            "packages",
            "reference_time",
        ]:
            assert "is not of type 'string'\n" in errors({k: {**v, prop: None}})


# namelist


def test_schema_namelist():
    errors = schema_validator("namelist")
    # Basic correctness (see also namelist_names_values test):
    assert not errors(
        {
            "namelist": {
                "array": [1, 2, 3],
                "boolean": True,
                "float": 3.14,
                "integer": 42,
                "string": "foo",
            }
        }
    )
    # Other types at the name-value level are not allowed:
    errormsg = "%s is not of type 'array', 'boolean', 'number', 'string'\n"
    assert errormsg % "None" in errors({"namelist": {"nonetype": None}})
    assert errormsg % "{}" in errors({"namelist": {"dict": {}}})
    # Needs at least one namelist value:
    assert "{} should be non-empty" in errors({})
    # Needs at least one name-value value:
    assert "{} should be non-empty" in errors({"namelist": {}})
    # Namelist level must be a mapping:
    assert "[] is not of type 'object'\n" in errors([])
    # Name-value level level must be a mapping:
    assert "[] is not of type 'object'\n" in errors({"namelist": []})


# orog


def test_schema_orog():
    config: dict = {
        "execution": {
            "executable": "/path/to/orog",
        },
        "grid_file": "/path/to/grid/file",
        "mask": False,
        "merge": "none",
        "old_line1_items": {
            "blat": 0,
            "efac": 0,
            "jcap": 0,
            "latb": 0,
            "lonb": 0,
            "mtnres": 1,
            "nr": 0,
            "nf1": 0,
            "nf2": 0,
        },
        "orog_file": "/path/to/orog/file",
        "rundir": "/path/to/run/dir",
    }

    errors = schema_validator("orog", "properties", "orog")
    # Basic correctness:
    assert not errors(config)
    # All 9 config keys are required:
    assert "does not have enough properties" in errors(with_del(config, "old_line1_items", "blat"))
    # Other config keys are not allowed:
    assert "Additional properties are not allowed" in errors(
        with_set(config, "bar", "old_line1_items", "foo")
    )
    # All old_line1_items keys require integer values:
    for key in config["old_line1_items"]:
        assert "is not of type 'integer'\n" in errors(
            with_set(config, None, "old_line1_items", key)
        )
    # Some top level keys are required:
    for key in ["execution", "grid_file", "rundir"]:
        assert f"'{key}' is a required property" in errors(with_del(config, key))
    # Other top-level keys are not allowed:
    assert "Additional properties are not allowed" in errors(with_set(config, "bar", "foo"))
    # The mask key requires boolean values:
    assert "is not of type 'boolean'\n" in errors({"mask": None})
    # Top-level keys require a string value:
    for key in ["grid_file", "rundir", "merge", "orog_file"]:
        assert "is not of type 'string'\n" in errors(with_set(config, None, "rundir"))


# orog-gsl


def test_schema_orog_gsl():
    config = {
        "config": {
            "halo": 4,
            "input_grid_file": "/path/to/gridfile",
            "resolution": 304,
            "tile": 7,
            "topo_data_2p5m": "/path/to/topo2p5m",
            "topo_data_30s": "/path/to/topo30s",
        },
        "execution": {
            "executable": "/path/to/orog_gsl",
        },
        "rundir": "/path/to/run/dir",
    }
    errors = schema_validator("orog-gsl", "properties", "orog_gsl")
    # Basic correctness:
    assert not errors(config)
    # All config keys are requried:
    for key in ["halo", "input_grid_file", "resolution", "tile", "topo_data_2p5m", "topo_data_30s"]:
        assert f"'{key}' is a required property" in errors(with_del(config, "config", key))
    # Other config keys are not allowed:
    assert "Additional properties are not allowed" in errors(
        with_set(config, "bar", "config", "foo")
    )
    # Some config keys require integer values:
    for key in ["halo", "resolution", "tile"]:
        assert "is not of type 'integer'\n" in errors(with_set(config, None, "config", key))
    # Some config keys require string values:
    for key in ["input_grid_file", "topo_data_2p5m", "topo_data_30s"]:
        assert "is not of type 'string'\n" in errors(with_set(config, None, "config", key))
    # Some top level keys are required:
    for key in ["config", "execution", "rundir"]:
        assert f"'{key}' is a required property" in errors(with_del(config, key))
    # Other top-level keys are not allowed:
    assert "Additional properties are not allowed" in errors(with_set(config, "bar", "foo"))
    # Top-level rundir key requires a string value:
    assert "is not of type 'string'\n" in errors(with_set(config, None, "rundir"))


# platform


def test_schema_platform():
    config = {"account": "me", "scheduler": "slurm"}
    errors = schema_validator("platform", "properties", "platform")
    # Basic correctness:
    assert not errors(config)
    # Extra top-level keys are forbidden:
    assert "Additional properties are not allowed" in errors(with_set(config, "bar", "foo"))
    # There is a fixed set of supported schedulers:
    assert "'foo' is not one of ['lsf', 'pbs', 'slurm']" in errors(
        with_set(config, "foo", "scheduler")
    )
    # account and scheduler are optional:
    assert not errors({})
    # account is required if scheduler is specified:
    assert "'account' is a dependency of 'scheduler'" in errors(with_del(config, "account"))
    # scheduler is required if account is specified:
    assert "'scheduler' is a dependency of 'account'" in errors(with_del(config, "scheduler"))


# rocoto


def test_schema_rocoto_compoundTimeString():
    errors = schema_validator("rocoto", "$defs", "compoundTimeString")
    # Just a string is ok:
    assert not errors("foo")
    # An int value is ok:
    assert not errors(20240103120000)
    # A simple cycle string is ok:
    assert not errors({"cyclestr": {"value": "@Y@m@d@H"}})
    # The "value" entry is required:
    assert "is not valid" in errors({"cyclestr": {}})
    # Unknown properties are not allowed:
    assert "is not valid" in errors({"cyclestr": {"foo": "bar"}})
    # An "offset" attribute may be provided:
    assert not errors({"cyclestr": {"value": "@Y@m@d@H", "attrs": {"offset": "06:00:00"}}})
    # The "offset" value must be a valid time string:
    assert "is not valid" in errors({"cyclestr": {"value": "@Y@m@d@H", "attrs": {"offset": "x"}}})


def test_schema_rocoto_dependency_sh():
    errors = schema_validator("rocoto", "$defs", "dependency")
    # Basic spec:
    assert not errors({"sh": {"command": "foo"}})
    # The "command" property is mandatory:
    assert "command' is a required property" in errors({"sh": {}})
    # A _<name> suffix is allowed:
    assert not errors({"sh_foo": {"command": "foo"}})
    # Optional attributes "runopt" and "shell" are supported:
    assert not errors(
        {"sh_foo": {"attrs": {"runopt": "-c", "shell": "/bin/bash"}, "command": "foo"}}
    )
    # Other attributes are not allowed:
    assert "Additional properties are not allowed ('color' was unexpected)" in errors(
        {"sh_foo": {"attrs": {"color": "blue"}, "command": "foo"}}
    )
    # The command is a compoundTimeString:
    assert not errors({"sh": {"command": {"cyclestr": {"value": "foo-@Y@m@d@H"}}}})


def test_schema_rocoto_metatask_attrs():
    errors = schema_validator("rocoto", "$defs", "metatask", "properties", "attrs")
    # Valid modes are "parallel" and "serial":
    assert not errors({"mode": "parallel"})
    assert not errors({"mode": "serial"})
    assert "'foo' is not one of ['parallel', 'serial']" in errors({"mode": "foo"})
    # Positive int is ok for throttle:
    assert not errors({"throttle": 42})
    assert not errors({"throttle": 0})
    assert "-1 is less than the minimum of 0" in errors({"throttle": -1})
    assert "'foo' is not of type 'integer'\n" in errors({"throttle": "foo"})


def test_schema_rocoto_workflow_cycledef():
    errors = schema_validator("rocoto", "properties", "workflow", "properties", "cycledef")
    # Basic spec:
    spec = "202311291200 202312011200 06:00:00"
    assert not errors([{"spec": spec}])
    # Spec with step specified as seconds:
    assert not errors([{"spec": "202311291200 202312011200 3600"}])
    # Basic spec with group attribute:
    assert not errors([{"attrs": {"group": "g"}, "spec": spec}])
    # Spec with positive activation offset attribute:
    assert not errors([{"attrs": {"activation_offset": "12:00:00"}, "spec": spec}])
    # Spec with negative activation offset attribute:
    assert not errors([{"attrs": {"activation_offset": "-12:00:00"}, "spec": spec}])
    # Spec with activation offset specified as positive seconds:
    assert not errors([{"attrs": {"activation_offset": 3600}, "spec": spec}])
    # Spec with activation offset specified as negative seconds:
    assert not errors([{"attrs": {"activation_offset": -3600}, "spec": spec}])
    # Property spec is required:
    assert "'spec' is a required property" in errors([{}])
    # Additional properties are not allowed:
    assert "'foo' was unexpected" in errors([{"spec": spec, "foo": "bar"}])
    # Additional attributes are not allowed:
    assert "'foo' was unexpected" in errors([{"attrs": {"foo": "bar"}, "spec": spec}])
    # Bad spec:
    assert "'x 202312011200 06:00:00' is not valid" in errors([{"spec": "x 202312011200 06:00:00"}])
    # Spec with bad activation offset attribute:
    assert "'foo' is not valid" in errors([{"attrs": {"activation_offset": "foo"}, "spec": spec}])


def test_schema_rocoto_task_resources():
    errors = schema_validator("rocoto", "$defs", "task", "properties")
    # Basic resource options
    assert not errors([{"cores": 1}])
    assert not errors([{"native": "abc"}])
    assert not errors([{"native": {"cyclestr": {"value": "def"}}}])
    assert not errors([{"nodes": "1:ppn=12"}])
    # Combined valid resources
    assert not errors([{"cores": 1, "native": "abc"}])
    assert not errors([{"native": "abc", "nodes": "1:ppn=12"}])


# schism


def test_schema_schism():
    config = {
        "namelist": {
            "template_file": "/tmp/param.nml",
            "template_values": {
                "dt": 100,
            },
        },
        "rundir": "/tmp",
    }
    errors = schema_validator("schism", "properties", "schism")
    # Basic correctness:
    assert not errors(config)
    # All top-level keys are required:
    for key in ("namelist", "rundir"):
        assert f"'{key}' is a required property" in errors(with_del(config, key))
    # Additional top-level keys are not allowed:
    assert "Additional properties are not allowed" in errors({**config, "foo": "bar"})


def test_schema_schism_namelist(schism_prop):
    errors = schism_prop("namelist")
    # At least template_file is required:
    assert "'template_file' is a required property" in errors({})
    # Just template_file is ok:
    assert not errors({"template_file": "/path/to/param.nml"})
    # Both template_file and template_values are ok:
    assert not errors(
        {
            "template_file": "/path/to/param.nml",
            "template_values": {"dt": 100},
        }
    )


def test_schema_schism_rundir(schism_prop):
    errors = schism_prop("rundir")
    # Must be a string:
    assert not errors("/some/path")
    assert "42 is not of type 'string'\n" in errors(42)


# sfc-climo-gen


def test_schema_sfc_climo_gen():
    config = {
        "execution": {"executable": "sfc_climo_gen"},
        "namelist": {"base_file": "/path", "validate": True},
        "rundir": "/tmp",
    }
    errors = schema_validator("sfc-climo-gen", "properties", "sfc_climo_gen")
    # Basic correctness:
    assert not errors(config)
    # Some top-level keys are required:
    for key in ("execution", "namelist", "rundir"):
        assert f"'{key}' is a required property" in errors(with_del(config, key))
    # Additional top-level keys are not allowed:
    assert "Additional properties are not allowed" in errors({**config, "foo": "bar"})


def test_schema_sfc_climo_gen_namelist(sfc_climo_gen_prop):
    base_file = {"base_file": "/some/path"}
    update_values = {"update_values": {"config": {"var": "val"}}}
    errors = sfc_climo_gen_prop("namelist")
    # Just base_file is ok:
    assert not errors(base_file)
    # base_file must be a string:
    assert "42 is not of type 'string'\n" in errors({"base_file": 42})
    # Just update_values is ok:
    assert not errors(update_values)
    # config is required with update_values:
    assert "'config' is a required property" in errors({"update_values": {}})
    # A combination of base_file and update_values is ok:
    assert not errors({**base_file, **update_values})
    # At least one is required:
    assert "is not valid" in errors({})


def test_schema_sfc_climo_gen_namelist_update_values(sfc_climo_gen_prop):
    errors = sfc_climo_gen_prop("namelist", "properties", "update_values", "properties", "config")
    # array, boolean, number, and string values are ok:
    assert not errors({"array": [1, 2, 3], "bool": True, "int": 42, "float": 3.14, "string": "foo"})
    # Other types are not, e.g.:
    assert "None is not of type 'array', 'boolean', 'number', 'string'\n" in errors({"null": None})
    # No minimum number of entries is required:
    assert not errors({})


def test_schema_sfc_climo_gen_rundir(sfc_climo_gen_prop):
    errors = sfc_climo_gen_prop("rundir")
    # Must be a string:
    assert not errors("/some/path")
    assert "42 is not of type 'string'\n" in errors(42)


# shave


def test_schema_shave():
    config = {
        "config": {
            "input_grid_file": "/path/to/input_grid_file",
            "output_grid_file": "/path/to/output_grid_file",
            "nx": 42,
            "ny": 42,
            "nhalo": 1,
        },
        "execution": {"executable": "shave"},
        "rundir": "/tmp",
    }
    errors = schema_validator("shave", "properties", "shave")
    # Basic correctness:
    assert not errors(config)
    # All top-level keys are required:
    for key in ("config", "execution", "rundir"):
        assert f"'{key}' is a required property" in errors(with_del(config, key))
    # Additional top-level keys are not allowed:
    assert "Additional properties are not allowed" in errors({**config, "foo": "bar"})


def test_schema_shave_config_properties():
    # Get errors function from schema_validator
    errors = schema_validator("shave", "properties", "shave", "properties", "config")
    for key in ("input_grid_file", "nx", "ny", "nhalo"):
        # All config keys are required:
        assert f"'{key}' is a required property" in errors({})
        # A string value is ok for input_grid_file:
        if key == "input_grid_file":
            assert "not of type 'string'" in str(errors({key: 42}))
        # nx, ny, and nhalo must be integers >= their respective minimum values:
        elif key in (keyvals := {"nx": 1, "ny": 1, "nhalo": 0}):
            minval = keyvals[key]
            assert "not of type 'integer'" in str(errors({key: "/path/"}))
            assert f"{minval - 1} is less than the minimum of {minval}" in str(
                errors({key: minval - 1})
            )
        # It is an error for the value to be a floating-point value:
        assert "not of type" in str(errors({key: 3.14}))
        # It is an error not to supply a value:
        assert "None is not of type" in str(errors({key: None}))


def test_schema_shave_rundir(shave_prop):
    errors = shave_prop("rundir")
    # Must be a string:
    assert not errors("/some/path")
    assert "42 is not of type 'string'\n" in errors(42)


# ungrib


def test_schema_ungrib():
    config = {
        "execution": {"executable": "/tmp/ungrib.exe"},
        "gfs_files": {
            "forecast_length": 24,
            "interval_hours": 6,
            "offset": 0,
            "path": "/tmp/gfs.t12z.pgrb2.0p25.f000",
        },
        "rundir": "/tmp",
        "vtable": "/tmp/Vtable.GFS",
    }
    errors = schema_validator("ungrib", "properties", "ungrib")
    # Basic correctness:
    assert not errors(config)
    # All top-level keys are required:
    for key in ("execution", "gfs_files", "rundir", "vtable"):
        assert f"'{key}' is a required property" in errors(with_del(config, key))
    # Additional top-level keys are not allowed:
    assert "Additional properties are not allowed" in errors({**config, "foo": "bar"})


def test_schema_ungrib_rundir(ungrib_prop):
    errors = ungrib_prop("rundir")
    # Must be a string:
    assert not errors("/some/path")
    assert "42 is not of type 'string'\n" in errors(42)


# upp


def test_schema_upp():
    config = {
        "execution": {
            "batchargs": {
                "cores": 1,
                "walltime": "00:01:00",
            },
            "executable": "/path/to/upp.exe",
        },
        "namelist": {
            "base_file": "/path/to/base.nml",
            "update_values": {
                "model_inputs": {
                    "grib": "grib2",
                },
                "nampgb": {
                    "kpo": 3,
                },
            },
            "validate": True,
        },
        "rundir": "/path/to/run",
    }
    errors = schema_validator("upp", "properties", "upp")
    # Basic correctness:
    assert not errors(config)
    # Some top-level keys are required:
    for key in ("execution", "namelist", "rundir"):
        assert f"'{key}' is a required property" in errors(with_del(config, key))
    # Other top-level keys are optional:
    assert not errors({**config, "files_to_copy": {"dst": "src"}})
    assert not errors({**config, "files_to_link": {"dst": "src"}})
    # Additional top-level keys are not allowed:
    assert "Additional properties are not allowed" in errors({**config, "foo": "bar"})


def test_schema_upp_namelist(upp_prop):
    maxpathlen = 256
    errors = upp_prop("namelist")
    # At least one of base_file or update_values is required:
    assert "is not valid" in errors({})
    # Just base_file is ok:
    assert not errors({"base_file": "/path/to/base.nml"})
    # Just update_values is ok:
    assert not errors({"update_values": {"model_inputs": {"grib": "grib2"}}})
    # Both base_file and update_values are ok:
    assert not errors(
        {"base_file": "/path/to/base.nml", "update_values": {"model_inputs": {"grib": "grib2"}}}
    )
    # Only two specific namelists are allowed:
    assert "Additional properties are not allowed" in errors(
        {"udpate_values": {"another_namelist": {}}}
    )
    # model_inputs: datestr requires a specific format:
    assert not errors({"update_values": {"model_inputs": {"datestr": "2024-05-06_12:00:00"}}})
    assert "does not match" in errors(
        {"update_values": {"model_inputs": {"datestr": "2024-05-06T12:00:00"}}}
    )
    # model_inputs: String pathnames have a max length:
    for key in ["filename", "filenameflat", "filenameflux"]:
        assert not errors({"update_values": {"model_inputs": {key: "c" * maxpathlen}}})
        assert "too long" in errors(
            {"update_values": {"model_inputs": {key: "c" * (maxpathlen + 1)}}}
        )
        assert "not of type 'string'" in errors({"update_values": {"model_inputs": {key: 42}}})
    # model_inputs: Only one grib value is supported:
    assert "not one of ['grib2']" in errors({"update_values": {"model_inputs": {"grib": "grib1"}}})
    assert "not of type 'string'" in errors({"update_values": {"model_inputs": {"grib": 42}}})
    # model_inputs: Only certain ioform values are supported:
    assert "not one of ['binarynemsio', 'netcdf']" in errors(
        {"update_values": {"model_inputs": {"ioform": "jpg"}}}
    )
    # model_inputs: Only certain modelname values are supported:
    assert "not one of ['FV3R', '3DRTMA', 'GFS', 'RAPR', 'NMM']" in errors(
        {"update_values": {"model_inputs": {"modelname": "foo"}}}
    )
    # model_inputs: Only certain submodelname values are supported:
    assert "not one of ['MPAS', 'RTMA']" in errors(
        {"update_values": {"model_inputs": {"submodelname": "foo"}}}
    )
    # model_inputs: No other keys are supported:
    assert "Additional properties are not allowed" in errors(
        {"update_values": {"model_inputs": {"something": "else"}}}
    )
    # nampgb: Some boolean keys are supported:
    for key in [
        "aqf_on",
        "d2d_chem",
        "gccpp_on",
        "gocart_on",
        "gtg_on",
        "hyb_sigp",
        "method_blsn",
        "nasa_on",
        "popascal",
        "rdaod",
        "slrutah_on",
        "write_ifi_debug_files",
    ]:
        assert not errors({"update_values": {"nampgb": {key: True}}})
        assert "not of type 'boolean'" in errors({"update_values": {"nampgb": {key: 42}}})
    # nampgb: String pathnames have a max length:
    for key in ["filenameaer"]:
        assert not errors({"update_values": {"nampgb": {key: "c" * maxpathlen}}})
        assert "too long" in errors({"update_values": {"nampgb": {key: "c" * (maxpathlen + 1)}}})
        assert "not of type 'string'" in errors({"update_values": {"nampgb": {key: 42}}})
    # nampgb: Some integer keys are supported:
    for key in ["kpo", "kpv", "kth", "numx"]:
        assert not errors({"update_values": {"nampgb": {key: 42}}})
        assert "not of type 'integer'" in errors({"update_values": {"nampgb": {key: True}}})
    # nampgb: Some arrays of numbers are supported:
    nitems = 70
    for key in ["po", "pv", "th"]:
        assert not errors({"update_values": {"nampgb": {key: [3.14] * nitems}}})
        assert "too long" in errors({"update_values": {"nampgb": {key: [3.14] * (nitems + 1)}}})
        assert "not of type 'number'" in errors(
            {"update_values": {"nampgb": {key: [True] * nitems}}}
        )
    # nampgb: Only one vtimeunits value is supported:
    assert "not one of ['FMIN']" in errors({"update_values": {"nampgb": {"vtimeunits": "FOO"}}})
    # nampgb: No other keys are supported:
    assert "Additional properties are not allowed" in errors(
        {"update_values": {"nampgb": {"something": "else"}}}
    )


def test_schema_upp_rundir(upp_prop):
    errors = upp_prop("rundir")
    # Must be a string:
    assert not errors("/some/path")
    assert "42 is not of type 'string'\n" in errors(42)


# ww3


def test_schema_ww3():
    config = {
        "namelist": {
            "template_file": "/tmp/ww3_shel.nml",
            "template_values": {
                "input_forcing_winds": "C",
            },
        },
        "rundir": "/tmp",
    }
    errors = schema_validator("ww3", "properties", "ww3")
    # Basic correctness:
    assert not errors(config)
    # All top-level keys are required:
    for key in ("namelist", "rundir"):
        assert f"'{key}' is a required property" in errors(with_del(config, key))
    # Additional top-level keys are not allowed:
    assert "Additional properties are not allowed" in errors({**config, "foo": "bar"})


def test_schema_ww3_namelist(ww3_prop):
    errors = ww3_prop("namelist")
    # At least template_file is required:
    assert "'template_file' is a required property" in errors({})
    # Just template_file is ok:
    assert not errors({"template_file": "/path/to/ww3_shel.nml"})
    # Both template_file and template_values are ok:
    assert not errors(
        {
            "template_file": "/path/to/ww3_shel.nml",
            "template_values": {"input_forcing_winds": "C"},
        }
    )


def test_schema_ww3_rundir(ww3_prop):
    errors = ww3_prop("rundir")
    # Must be a string:
    assert not errors("/some/path")
    assert "42 is not of type 'string'\n" in errors(42)
