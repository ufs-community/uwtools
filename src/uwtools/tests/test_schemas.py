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
def sfc_climo_gen_prop():
    return partial(schema_validator, "sfc-climo-gen", "properties", "sfc_climo_gen", "properties")


@fixture
def ungrib_prop():
    return partial(schema_validator, "ungrib", "properties", "ungrib", "properties")


@fixture
def update_values():
    return {
        "update_values": {
            "regional_grid_nml": {
                "delx": 0.22,
                "dely": 0.22,
                "lx": -200,
                "ly": -130,
                "pazi": 0.0,
                "plat": 45.5,
                "plon": -100.5,
            }
        }
    }


# chgres-cube


def test_schema_chgres_cube():
    config = {
        "execution": {"executable": "chgres_cube"},
        "run_dir": "/tmp",
    }
    errors = schema_validator("chgres-cube", "properties", "chgres_cube")
    # Basic correctness:
    assert not errors(config)
    # Some top-level keys are required:
    for key in ("execution", "run_dir"):
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
        "run_dir": "/tmp",
    }
    errors = schema_validator("esg-grid", "properties", "esg_grid")
    # Basic correctness:
    assert not errors(config)
    # Some top-level keys are required:
    for key in ("execution", "run_dir"):
        assert f"'{key}' is a required property" in errors(with_del(config, key))
    # Additional top-level keys are not allowed:
    assert "Additional properties are not allowed" in errors({**config, "foo": "bar"})
    # Additional MPI support is not allowed:
    assert "Additional properties are not allowed ('mpicmd' was unexpected)" in errors(
        {"execution": {"mpicmd": "srun"}}
    )


def test_schema_esg_grid_namelist(esg_grid_prop, update_values):
    base_file = {"base_file": "/some/path"}
    errors = esg_grid_prop("namelist")
    # Just base_file is ok:
    assert not errors(base_file)
    # base_file must be a string:
    assert "{'base_file': 88} is not valid under any of the given schemas" in errors(
        {"base_file": 88}
    )
    # Just update_values is ok:
    assert not errors(update_values)
    # A combination of base_file and update_values is ok:
    assert not errors({**base_file, **update_values})
    # All key/value pairs in update_values must be present if base_file is not supplied:
    assert "is not valid under any of the given schemas" in errors(
        with_del(update_values, "update_values", "regional_grid_nml", "delx")
    )
    # Subsection of update_values is ok if base_file is supplied:
    assert not errors(
        {
            **base_file,
            "update_values": {"regional_grid_nml": {"delx": 0.11, "lx": -180, "plat": 38.0}},
        }
    )
    # regional_grid_nml is required with update_values:
    assert "{'update_values': {}} is not valid under any of the given schemas" in errors(
        with_del(update_values, "update_values", "regional_grid_nml")
    )
    # At least one is required:
    assert "is not valid" in errors({})


def test_schema_esg_grid_namelist_update_values(esg_grid_prop):
    config = {
        "base_file": "some/str",
        "update_values": {
            "regional_grid_nml": {
                "delx": 0.22,
                "dely": 0.22,
                "lx": -200,
                "ly": -130,
                "pazi": 0.0,
                "plat": 45.5,
                "plon": -100.5,
            }
        },
    }
    errors = esg_grid_prop("namelist")
    # Basic correctness:
    assert not errors(config)
    # A base_file with partial update_values is ok:
    assert not errors(with_del(config, "update_values", "regional_grid_nml", "delx"))
    # A completely-specified update_values with no base_file is ok:
    assert not errors(with_del(config, "base_file"))
    # A base_file with no update_values is ok:
    assert not errors(with_del(config, "update_values"))
    # It is an error to provide no base_file and only a partially-specified namelist:
    assert "is not valid under any of the given schemas" in errors(
        with_del(with_del(config, "base_file"), "update_values", "regional_grid_nml", "delx")
    )
    # update_values values must be a number:
    assert "is not valid under any of the given schemas" in errors(
        {"update_values": {"regional_grid_nml": {"delx": "/some/str"}}}
    )
    # It is an error to not provide at least one of base_file or update_values:
    assert "{} is not valid under any of the given schemas" in errors(
        with_del(with_del(config, "base_file"), "update_values")
    )


def test_schema_esg_grid_regional_grid_nml_properties():
    errors = partial(schema_validator("esg-grid", "$defs", "regional_grid_nml_properties"))
    # An integer value is ok:
    assert not errors({"delx": 88})
    # A floating-point value is ok:
    assert not errors({"delx": 3.14})
    # It is an error for the value to be of type string:
    assert "'foo' is not of type 'number'" in errors({"ly": "foo"})
    # It is an error not to supply a value:
    assert "{'delx'} is not of type 'object'" in errors({"delx"})


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
    # Basic correctness, empty map is ok:
    assert not errors({})
    # Managed properties are fine:
    assert not errors({"queue": "string", "walltime": "string"})
    # But so are unknown ones:
    assert not errors({"--foo": 88})
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
        "run_dir": "/tmp",
    }
    errors = schema_validator("fv3", "properties", "fv3")
    # Basic correctness:
    assert not errors(config)
    # Some top-level keys are required:
    for key in ("domain", "execution", "lateral_boundary_conditions", "length", "run_dir"):
        assert f"'{key}' is a required property" in errors(with_del(config, key))
    # Some top-level keys are optional:
    assert not errors(
        {
            **config,
            "diag_table": "/path",
            "files_to_copy": {"fn": "/path"},
            "files_to_link": {"fn": "/path"},
            "model_configure": {"base_file": "/path"},
            "namelist": {"base_file": "/path"},
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


# sfc-climo-gen


def test_schema_sfc_climo_gen():
    config = {
        "execution": {"executable": "sfc_climo_gen"},
        "run_dir": "/tmp",
    }
    errors = schema_validator("sfc-climo-gen", "properties", "sfc_climo_gen")
    # Basic correctness:
    assert not errors(config)
    # Some top-level keys are required:
    for key in ("execution", "run_dir"):
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
