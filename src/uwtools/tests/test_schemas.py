# pylint: disable=missing-function-docstring,redefined-outer-name
"""
Granular tests of JSON Schema schemas.
"""

from functools import partial

import pytest
from pytest import fixture

from uwtools.tests.support import schema_validator, with_del, with_set

# Fixtures


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
def sfc_climo_gen_prop():
    return partial(schema_validator, "sfc-climo-gen", "properties", "sfc_climo_gen", "properties")


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


# chgres-cube


def test_schema_chgres_cube():
    config = {
        "execution": {"executable": "chgres_cube"},
        "namelist": {"base_file": "/path", "validate": True},
        "run_dir": "/tmp",
    }
    errors = schema_validator("chgres-cube", "properties", "chgres_cube")
    # Basic correctness:
    assert not errors(config)
    # Some top-level keys are required:
    for key in ("execution", "namelist", "run_dir"):
        assert f"'{key}' is a required property" in errors(with_del(config, key))
    # Additional top-level keys are not allowed:
    assert "Additional properties are not allowed" in errors({**config, "foo": "bar"})


def test_schema_chgres_cube_namelist(chgres_cube_prop):
    base_file = {"base_file": "/some/path"}
    update_values = {"update_values": {"config": {"var": "val"}}}
    errors = chgres_cube_prop("namelist")
    # Just base_file is ok:
    assert not errors(base_file)
    # base_file must be a string:
    assert "88 is not of type 'string'" in errors({"base_file": 88})
    # Just update_values is ok:
    assert not errors(update_values)
    # config is required with update_values:
    assert "'config' is a required property" in errors({"update_values": {}})
    # A combination of base_file and update_values is ok:
    assert not errors({**base_file, **update_values})
    # At least one is required:
    assert "is not valid" in errors({})


def test_schema_chgres_cube_namelist_update_values(chgres_cube_prop):
    errors = chgres_cube_prop("namelist", "properties", "update_values", "properties", "config")
    # array, boolean, number, and string values are ok:
    assert not errors({"array": [1, 2, 3], "bool": True, "int": 88, "float": 3.14, "string": "foo"})
    # Other types are not, e.g.:
    assert "None is not of type 'array', 'boolean', 'number', 'string'" in errors({"null": None})
    # No minimum number of entries is required:
    assert not errors({})


def test_schema_chgres_cube_run_dir(chgres_cube_prop):
    errors = chgres_cube_prop("run_dir")
    # Must be a string:
    assert not errors("/some/path")
    assert "88 is not of type 'string'" in errors(88)


# esg-grid


def test_schema_esg_grid():
    config = {
        "execution": {"executable": "esg_grid"},
        "namelist": {"base_file": "/path", "validate": True},
        "run_dir": "/tmp",
    }
    errors = schema_validator("esg-grid", "properties", "esg_grid")
    # Basic correctness:
    assert not errors(config)
    # Some top-level keys are required:
    for key in ("execution", "namelist", "run_dir"):
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
    assert "not valid" in errors({**esg_namelist, "base_file": 88})
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


@pytest.mark.parametrize("key", ["delx", "dely", "lx", "ly", "pazi", "plat", "plon"])
def test_schema_esg_grid_namelist_content(key):
    config: dict = {
        "regional_grid_nml": {
            "delx": 88,
            "dely": 88,
            "lx": 88,
            "ly": 88,
            "pazi": 88,
            "plat": 88,
            "plon": 88,
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


def test_schema_esg_grid_run_dir(esg_grid_prop):
    errors = esg_grid_prop("run_dir")
    # Must be a string:
    assert not errors("/some/path")
    assert "88 is not of type 'string'" in errors(88)


# execution


def test_execution():
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


def test_execution_batchargs():
    errors = schema_validator("execution", "properties", "batchargs")
    # Basic correctness, only walltime is required:
    assert "'walltime' is a required property" in errors({})
    assert not errors({"walltime": "00:05:00"})
    # Managed properties are fine:
    assert not errors({"queue": "string", "walltime": "00:05:00"})
    # But so are unknown ones:
    assert not errors({"--foo": 88, "walltime": "00:05:00"})
    # It just has to be a map:
    assert "[] is not of type 'object'" in errors([])


def test_execution_executable():
    errors = schema_validator("execution", "properties", "executable")
    # String value is ok:
    assert not errors("fv3.exe")
    # Anything else is not:
    assert "88 is not of type 'string'" in errors(88)


def test_execution_mpiargs():
    errors = schema_validator("execution", "properties", "mpiargs")
    # Basic correctness:
    assert not errors(["string1", "string2"])
    # mpiargs may be empty:
    assert not errors([])
    # String values are expected:
    assert "88 is not of type 'string'" in errors(["string1", 88])


def test_execution_threads():
    errors = schema_validator("execution", "properties", "threads")
    # threads must be non-negative, and an integer:
    assert not errors(0)
    assert not errors(4)
    assert "-1 is less than the minimum of 0" in errors(-1)
    assert "3.14 is not of type 'integer'" in errors(3.14)


# execution-serial


def test_execution_serial():
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


def test_execution_serial_batchargs():
    test_execution_batchargs()


def test_execution_serial_executable():
    test_execution_batchargs()


# files-to-stage


def test_schema_files_to_stage():
    errors = schema_validator("files-to-stage")
    # The input must be an dict:
    assert "is not of type 'object'" in errors([])
    # A str -> str dict is ok:
    assert not errors({"file1": "/path/to/file1", "file2": "/path/to/file2"})
    # An empty dict is not allowed:
    assert "{} should be non-empty" in errors({})
    # Non-string values are not allowed:
    assert "True is not of type 'string'" in errors({"file1": True})


# fv3


def test_schema_fv3():
    config = {
        "domain": "regional",
        "execution": {"executable": "fv3"},
        "field_table": {"base_file": "/path"},
        "lateral_boundary_conditions": {"interval_hours": 1, "offset": 0, "path": "/tmp/file"},
        "length": 3,
        "namelist": {"base_file": "/path", "validate": True},
        "run_dir": "/tmp",
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
        "run_dir",
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
    assert "88 is not of type 'string'" in errors(88)


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
    assert "'s' is not of type 'integer'" in errors(with_set(config, "s", "interval_hours"))
    # offset must be an integer of at least 0:
    assert "-1 is less than the minimum of 0" in errors(with_set(config, -1, "offset"))
    assert "'s' is not of type 'integer'" in errors(with_set(config, "s", "offset"))
    # path must be a string:
    assert "88 is not of type 'string'" in errors(with_set(config, 88, "path"))


def test_schema_fv3_length(fv3_prop):
    errors = fv3_prop("length")
    # Positive int is ok:
    assert not errors(6)
    # Zero is not ok:
    assert "0 is less than the minimum of 1" in errors(0)
    # A negative number is not ok:
    assert "-1 is less than the minimum of 1" in errors(-1)
    # Something other than an int is not ok:
    assert "'a string' is not of type 'integer'" in errors("a string")


def test_schema_fv3_model_configure(fv3_prop):
    base_file = {"base_file": "/some/path"}
    update_values = {"update_values": {"foo": 88}}
    errors = fv3_prop("model_configure")
    # Just base_file is ok:
    assert not errors(base_file)
    # But base_file must be a string:
    assert "88 is not of type 'string'" in errors({"base_file": 88})
    # Just update_values is ok:
    assert not errors(update_values)
    # A combination of base_file and update_values is ok:
    assert not errors({**base_file, **update_values})
    # At least one is required:
    assert "is not valid" in errors({})


def test_schema_fv3_model_configure_update_values(fv3_prop):
    errors = fv3_prop("model_configure", "properties", "update_values")
    # boolean, number, and string values are ok:
    assert not errors({"bool": True, "int": 88, "float": 3.14, "string": "foo"})
    # Other types are not, e.g.:
    assert "None is not of type 'boolean', 'number', 'string'" in errors({"null": None})
    # At least one entry is required:
    assert "{} should be non-empty" in errors({})


def test_schema_fv3_namelist(fv3_prop):
    base_file = {"base_file": "/some/path"}
    update_values = {"update_values": {"nml": {"var": "val"}}}
    errors = fv3_prop("namelist")
    # Just base_file is ok:
    assert not errors(base_file)
    # base_file must be a string:
    assert "88 is not of type 'string'" in errors({"base_file": 88})
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
        {"nml": {"array": [1, 2, 3], "bool": True, "int": 88, "float": 3.14, "string": "foo"}}
    )
    # Other types are not, e.g.:
    assert "None is not of type 'array', 'boolean', 'number', 'string'" in errors(
        {"nml": {"null": None}}
    )
    # At least one namelist entry is required:
    assert "{} should be non-empty" in errors({})
    # At least one val/var pair is required:
    assert "{} should be non-empty" in errors({"nml": {}})


def test_schema_fv3_run_dir(fv3_prop):
    errors = fv3_prop("run_dir")
    # Must be a string:
    assert not errors("/some/path")
    assert "88 is not of type 'string'" in errors(88)


# global_equiv_resol


def test_schema_global_equiv_resol():
    config = {
        "execution": {"executable": "/tmp/global_equiv_resol.exe"},
        "input_grid_file": "/tmp/input_grid_file",
        "run_dir": "/tmp",
    }
    errors = schema_validator("global-equiv-resol", "properties", "global_equiv_resol")
    # Basic correctness:
    assert not errors(config)
    # All top-level keys are required:
    for key in ("execution", "input_grid_file", "run_dir"):
        assert f"'{key}' is a required property" in errors(with_del(config, key))
    # Additional top-level keys are not allowed:
    assert "Additional properties are not allowed" in errors({**config, "foo": "bar"})


@pytest.mark.parametrize("schema_entry", ["run_dir", "input_grid_file"])
def test_schema_global_equiv_resol_paths(global_equiv_resol_prop, schema_entry):
    errors = global_equiv_resol_prop(schema_entry)
    # Must be a string:
    assert not errors("/some/path")
    assert "88 is not of type 'string'" in errors(88)


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
        "run_dir": "/tmp",
    }
    errors = schema_validator("jedi", "properties", "jedi")
    # Basic correctness:
    assert not errors(config)
    # All top-level keys are required:
    for key in ("configuration_file", "execution", "run_dir"):
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


def test_schema_jedi_run_dir(jedi_prop):
    errors = jedi_prop("run_dir")
    # Must be a string:
    assert not errors("/some/path")
    assert "88 is not of type 'string'" in errors(88)


# make_hgrid


def test_schema_make_hgrid():
    config = {
        "config": {"grid_type": "from_file", "my_grid_file": "/path/to/my_grid_file"},
        "execution": {"executable": "make_hgrid"},
        "run_dir": "/tmp",
    }
    errors = schema_validator("make-hgrid", "properties", "make_hgrid")
    # Basic correctness:
    assert not errors(config)
    # All top-level keys are required:
    for key in ("config", "execution", "run_dir"):
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


def test_schema_make_hgrid_run_dir(make_hgrid_prop):
    errors = make_hgrid_prop("run_dir")
    # Must be a string:
    assert not errors("/some/path")
    assert "88 is not of type 'string'" in errors(88)


# make_solo_mosaic


def test_schema_make_solo_mosaic():
    config = {
        "config": {"dir": "path/to/dir", "num_tiles": 1},
        "execution": {"executable": "make_solo_mosaic"},
        "run_dir": "/tmp",
    }
    errors = schema_validator("make-solo-mosaic", "properties", "make_solo_mosaic")
    # Basic correctness:
    assert not errors(config)
    # All top-level keys are required:
    for key in ("config", "execution", "run_dir"):
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
            assert "not of type 'string'" in str(errors({key: 88}))
        # num_tiles must be an integer:
        else:
            assert "not of type 'integer'" in str(errors({key: "/path/"}))
        # It is an error for the value to be a floating-point value:
        assert "not of type" in str(errors({key: 3.14}))
        # It is an error not to supply a value:
        assert "None is not of type" in str(errors({key: None}))


def test_schema_make_solo_mosaic_run_dir(make_solo_mosaic_prop):
    errors = make_solo_mosaic_prop("run_dir")
    # Must be a string:
    assert not errors("/some/path")
    assert "88 is not of type 'string'" in errors(88)


# mpas


def test_schema_mpas():
    config = {
        "execution": {"executable": "atmosphere_model"},
        "namelist": {"base_file": "path/to/simple.nml", "validate": True},
        "run_dir": "path/to/rundir",
        "streams": {"path": "path/to/streams.atmosphere.in", "values": {"world": "user"}},
    }
    errors = schema_validator("mpas", "properties", "mpas")
    # Basic correctness:
    assert not errors(config)
    # All top-level keys are required:
    for key in ("execution", "namelist", "run_dir", "streams"):
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
    assert "'s' is not of type 'integer'" in errors(with_set(config, "s", "interval_hours"))
    # offset must be an integer of at least 0:
    assert "-1 is less than the minimum of 0" in errors(with_set(config, -1, "offset"))
    assert "'s' is not of type 'integer'" in errors(with_set(config, "s", "offset"))
    # path must be a string:
    assert "88 is not of type 'string'" in errors(with_set(config, 88, "path"))


def test_schema_mpas_length(mpas_prop):
    errors = mpas_prop("length")
    # Positive int is ok:
    assert not errors(6)
    # Zero is not ok:
    assert "0 is less than the minimum of 1" in errors(0)
    # A negative number is not ok:
    assert "-1 is less than the minimum of 1" in errors(-1)
    # Something other than an int is not ok:
    assert "'a string' is not of type 'integer'" in errors("a string")


def test_schema_mpas_namelist(mpas_prop):
    base_file = {"base_file": "/some/path"}
    update_values = {"update_values": {"nml": {"var": "val"}}}
    errors = mpas_prop("namelist")
    # Just base_file is ok:
    assert not errors(base_file)
    # base_file must be a string:
    assert "88 is not of type 'string'" in errors({"base_file": 88})
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
        {"nml": {"array": [1, 2, 3], "bool": True, "int": 88, "float": 3.14, "string": "foo"}}
    )
    # Other types are not, e.g.:
    assert "None is not of type 'array', 'boolean', 'number', 'string'" in errors(
        {"nml": {"null": None}}
    )
    # At least one namelist entry is required:
    assert "{} should be non-empty" in errors({})
    # At least one val/var pair is required:
    assert "{} should be non-empty" in errors({"nml": {}})


def test_schema_mpas_run_dir(mpas_prop):
    errors = mpas_prop("run_dir")
    # Must be a string:
    assert not errors("/some/path")
    assert "88 is not of type 'string'" in errors(88)


def test_schema_mpas_streams(mpas_prop):
    config = {"path": "/some/path", "values": {"nml": {"var": "val"}}}
    errors = mpas_prop("streams")
    # Basic correctness:
    assert not errors(config)
    # All streams items are required:
    assert "'path' is a required property" in errors(with_del(config, "path"))
    assert "'values' is a required property" in errors(with_del(config, "values"))
    # path must be a string:
    assert "1 is not of type 'string'" in errors(with_set(config, 1, "path"))
    # values must be an object:
    assert "1 is not of type 'object'" in errors(with_set(config, -1, "values"))
    assert "'s' is not of type 'object'" in errors(with_set(config, "s", "values"))


# mpas_init


def test_schema_mpas_init():
    config = {
        "execution": {"executable": "mpas_init"},
        "namelist": {"base_file": "path/to/simple.nml", "validate": True},
        "run_dir": "path/to/rundir",
        "streams": {"path": "path/to/streams.atmosphere.in", "values": {"world": "user"}},
    }
    errors = schema_validator("mpas-init", "properties", "mpas_init")
    # Basic correctness:
    assert not errors(config)
    # All top-level keys are required:
    for key in ("execution", "namelist", "run_dir", "streams"):
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
    assert "'s' is not of type 'integer'" in errors(with_set(config, "s", "interval_hours"))
    # offset must be an integer of at least 0:
    assert "-1 is less than the minimum of 0" in errors(with_set(config, -1, "offset"))
    assert "'s' is not of type 'integer'" in errors(with_set(config, "s", "offset"))
    # path must be a string:
    assert "88 is not of type 'string'" in errors(with_set(config, 88, "path"))
    # length must be a positive int
    assert "0 is less than the minimum of 1" in errors(with_set(config, 0, "length"))
    assert "-1 is less than the minimum of 1" in errors(with_set(config, -1, "length"))
    assert "'s' is not of type 'integer'" in errors(with_set(config, "s", "length"))


def test_schema_mpas_init_namelist(mpas_init_prop):
    base_file = {"base_file": "/some/path"}
    update_values = {"update_values": {"nml": {"var": "val"}}}
    errors = mpas_init_prop("namelist")
    # Just base_file is ok:
    assert not errors(base_file)
    # base_file must be a string:
    assert "88 is not of type 'string'" in errors({"base_file": 88})
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
        {"nml": {"array": [1, 2, 3], "bool": True, "int": 88, "float": 3.14, "string": "foo"}}
    )
    # Other types are not, e.g.:
    assert "None is not of type 'array', 'boolean', 'number', 'string'" in errors(
        {"nml": {"null": None}}
    )
    # At least one namelist entry is required:
    assert "{} should be non-empty" in errors({})
    # At least one val/var pair is required:
    assert "{} should be non-empty" in errors({"nml": {}})


def test_schema_mpas_init_run_dir(mpas_init_prop):
    errors = mpas_init_prop("run_dir")
    # Must be a string:
    assert not errors("/some/path")
    assert "88 is not of type 'string'" in errors(88)


def test_schema_mpas_init_streams(mpas_init_prop):
    config = {"path": "/some/path", "values": {"nml": {"var": "val"}}}
    errors = mpas_init_prop("streams")
    # Basic correctness:
    assert not errors(config)
    # All streams items are required:
    assert "'path' is a required property" in errors(with_del(config, "path"))
    assert "'values' is a required property" in errors(with_del(config, "values"))
    # path must be a string:
    assert "1 is not of type 'string'" in errors(with_set(config, 1, "path"))
    # values must be an object:
    assert "1 is not of type 'object'" in errors(with_set(config, -1, "values"))
    assert "'s' is not of type 'object'" in errors(with_set(config, "s", "values"))


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
                "integer": 88,
                "string": "foo",
            }
        }
    )
    # Other types at the name-value level are not allowed:
    errormsg = "%s is not of type 'array', 'boolean', 'number', 'string'"
    assert errormsg % "None" in errors({"namelist": {"nonetype": None}})
    assert errormsg % "{}" in errors({"namelist": {"dict": {}}})
    # Needs at least one namelist value:
    assert "{} should be non-empty" in errors({})
    # Needs at least one name-value value:
    assert "{} should be non-empty" in errors({"namelist": {}})
    # Namelist level must be a mapping:
    assert "[] is not of type 'object'" in errors([])
    # Name-value level level must be a mapping:
    assert "[] is not of type 'object'" in errors({"namelist": []})


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
    assert not errors({"throttle": 88})
    assert not errors({"throttle": 0})
    assert "-1 is less than the minimum of 0" in errors({"throttle": -1})
    assert "'foo' is not of type 'integer'" in errors({"throttle": "foo"})


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


# sfc-climo-gen


def test_schema_sfc_climo_gen():
    config = {
        "execution": {"executable": "sfc_climo_gen"},
        "namelist": {"base_file": "/path", "validate": True},
        "run_dir": "/tmp",
    }
    errors = schema_validator("sfc-climo-gen", "properties", "sfc_climo_gen")
    # Basic correctness:
    assert not errors(config)
    # Some top-level keys are required:
    for key in ("execution", "namelist", "run_dir"):
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
    assert "88 is not of type 'string'" in errors({"base_file": 88})
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
    assert not errors({"array": [1, 2, 3], "bool": True, "int": 88, "float": 3.14, "string": "foo"})
    # Other types are not, e.g.:
    assert "None is not of type 'array', 'boolean', 'number', 'string'" in errors({"null": None})
    # No minimum number of entries is required:
    assert not errors({})


def test_schema_sfc_climo_gen_run_dir(sfc_climo_gen_prop):
    errors = sfc_climo_gen_prop("run_dir")
    # Must be a string:
    assert not errors("/some/path")
    assert "88 is not of type 'string'" in errors(88)


# shave


def test_schema_shave():
    config = {
        "config": {
            "input_grid_file": "/path/to/input_grid_file",
            "nx": 88,
            "ny": 88,
            "nh4": 1,
        },
        "execution": {"executable": "shave"},
        "run_dir": "/tmp",
    }
    errors = schema_validator("shave", "properties", "shave")
    # Basic correctness:
    assert not errors(config)
    # All top-level keys are required:
    for key in ("config", "execution", "run_dir"):
        assert f"'{key}' is a required property" in errors(with_del(config, key))
    # Additional top-level keys are not allowed:
    assert "Additional properties are not allowed" in errors({**config, "foo": "bar"})


def test_schema_shave_config_properties():
    # Get errors function from schema_validator
    errors = schema_validator("shave", "properties", "shave", "properties", "config")
    for key in ("input_grid_file", "nx", "ny", "nh4"):
        # All config keys are required:
        assert f"'{key}' is a required property" in errors({})
        # A string value is ok for input_grid_file:
        if key == "input_grid_file":
            assert "not of type 'string'" in str(errors({key: 88}))
        # nx, ny, and nh4 must be positive integers:
        elif key in ["nx", "ny", "nh4"]:
            assert "not of type 'integer'" in str(errors({key: "/path/"}))
            assert "0 is less than the minimum of 1" in str(errors({key: 0}))
        # It is an error for the value to be a floating-point value:
        assert "not of type" in str(errors({key: 3.14}))
        # It is an error not to supply a value:
        assert "None is not of type" in str(errors({key: None}))


def test_schema_shave_run_dir(shave_prop):
    errors = shave_prop("run_dir")
    # Must be a string:
    assert not errors("/some/path")
    assert "88 is not of type 'string'" in errors(88)


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
        "run_dir": "/tmp",
        "vtable": "/tmp/Vtable.GFS",
    }
    errors = schema_validator("ungrib", "properties", "ungrib")
    # Basic correctness:
    assert not errors(config)
    # All top-level keys are required:
    for key in ("execution", "gfs_files", "run_dir", "vtable"):
        assert f"'{key}' is a required property" in errors(with_del(config, key))
    # Additional top-level keys are not allowed:
    assert "Additional properties are not allowed" in errors({**config, "foo": "bar"})


def test_schema_ungrib_run_dir(ungrib_prop):
    errors = ungrib_prop("run_dir")
    # Must be a string:
    assert not errors("/some/path")
    assert "88 is not of type 'string'" in errors(88)


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
        "run_dir": "/path/to/run",
    }
    errors = schema_validator("upp", "properties", "upp")
    # Basic correctness:
    assert not errors(config)
    # Some top-level keys are required:
    for key in ("execution", "namelist", "run_dir"):
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
        assert "not of type 'string'" in errors({"update_values": {"model_inputs": {key: 88}}})
    # model_inputs: Only one grib value is supported:
    assert "not one of ['grib2']" in errors({"update_values": {"model_inputs": {"grib": "grib1"}}})
    assert "not of type 'string'" in errors({"update_values": {"model_inputs": {"grib": 88}}})
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
        assert "not of type 'boolean'" in errors({"update_values": {"nampgb": {key: 88}}})
    # nampgb: String pathnames have a max length:
    for key in ["filenameaer"]:
        assert not errors({"update_values": {"nampgb": {key: "c" * maxpathlen}}})
        assert "too long" in errors({"update_values": {"nampgb": {key: "c" * (maxpathlen + 1)}}})
        assert "not of type 'string'" in errors({"update_values": {"nampgb": {key: 88}}})
    # nampgb: Some integer keys are supported:
    for key in ["kpo", "kpv", "kth", "numx"]:
        assert not errors({"update_values": {"nampgb": {key: 88}}})
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


def test_schema_upp_run_dir(upp_prop):
    errors = upp_prop("run_dir")
    # Must be a string:
    assert not errors("/some/path")
    assert "88 is not of type 'string'" in errors(88)


# ungrib


def test_schema_ww3():
    config = {
        "namelist": {
            "template_file": "/tmp/ww3_shel.nml",
            "template_values": {
                "input_forcing_winds": "C",
            },
        },
        "run_dir": "/tmp",
    }
    errors = schema_validator("ww3", "properties", "ww3")
    # Basic correctness:
    assert not errors(config)
    # All top-level keys are required:
    for key in ("namelist", "run_dir"):
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


def test_schema_ww3_run_dir(ww3_prop):
    errors = ww3_prop("run_dir")
    # Must be a string:
    assert not errors("/some/path")
    assert "88 is not of type 'string'" in errors(88)
