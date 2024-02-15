# pylint: disable=missing-function-docstring,redefined-outer-name

from functools import partial

from pytest import fixture

from uwtools.tests.support import schema_validator, with_del, with_set

# fv3


@fixture
def fv3_field_table_vals():
    return (
        {
            "foo": {
                "longname": "foofoo",
                "profile_type": {"name": "fixed", "surface_value": 1},
                "units": "cubits",
            }
        },
        {
            "bar": {
                "longname": "barbar",
                "profile_type": {"name": "profile", "surface_value": 2, "top_value": 3},
                "units": "rods",
            }
        },
    )


@fixture
def fv3_fcstprop():
    return partial(schema_validator, "fv3", "properties", "fv3", "properties")


def test_schema_fv3_defs_filesToStage():
    errors = schema_validator("fv3", "$defs", "filesToStage")
    # The input must be an dict:
    assert "is not of type 'object'" in errors([])
    # A str -> str dict is ok:
    assert not errors({"file1": "/path/to/file1", "file2": "/path/to/file2"})
    # An empty dict is not allowed:
    assert "does not have enough properties" in errors({})
    # Non-string values are not allowed:
    assert "True is not of type 'string'" in errors({"file1": True})


def test_schema_fv3_defs_namelist():
    errors = schema_validator("fv3", "$defs", "namelist")
    # Basic correctness (see also namelist_names_values test):
    assert not errors({"namelist": {"string": "foo"}})
    # Needs at least one value:
    assert "does not have enough properties" in errors({})
    # Must be a mapping:
    assert "[] is not of type 'object'" in errors([])


def test_schema_fv3_defs_namelist_names_values():
    errors = schema_validator("fv3", "$defs", "namelist_names_values")
    # Basic correctness:
    assert not errors(
        {"array": [1, 2, 3], "boolean": True, "float": 3.14, "integer": 88, "string": "foo"}
    )
    # Other types are not allowed:
    errormsg = "%s is not of type 'array', 'boolean', 'number', 'string'"
    assert errormsg % "None" in errors({"nonetype": None})
    assert errormsg % "{}" in errors({"dict": {}})
    # Needs at least one value:
    assert "does not have enough properties" in errors({})
    # Must be a mapping:
    assert "[] is not of type 'object'" in errors([])


def test_schema_fv3():
    d = {
        "domain": "regional",
        "execution": {"executable": "fv3"},
        "lateral_boundary_conditions": {"interval_hours": 1, "offset": 0, "path": "/tmp/file"},
        "length": 3,
        "run_dir": "/tmp",
    }
    errors = schema_validator("fv3", "properties", "fv3")
    # Basic correctness:
    assert not errors(d)
    # Some top-level keys are required:
    for key in ("domain", "execution", "lateral_boundary_conditions", "length", "run_dir"):
        assert f"'{key}' is a required property" in errors(with_del(d, key))
    # Some top-level keys are optional:
    assert not errors(
        {
            **d,
            "diag_table": "/path",
            "field_table": {"base_file": "/path"},
            "files_to_copy": {"fn": "/path"},
            "files_to_link": {"fn": "/path"},
            "model_configure": {"base_file": "/path"},
            "namelist": {"base_file": "/path"},
        }
    )
    # Additional top-level keys are not allowed:
    assert "Additional properties are not allowed" in errors({**d, "foo": "bar"})


def test_schema_fv3_diag_table(fv3_fcstprop):
    errors = fv3_fcstprop("diag_table")
    # String value is ok:
    assert not errors("/path/to/file")
    # Anything else is not:
    assert "88 is not of type 'string'" in errors(88)


def test_schema_fv3_domain(fv3_fcstprop):
    errors = fv3_fcstprop("domain")
    # There is a fixed set of domain values:
    assert "'foo' is not one of ['global', 'regional']" in errors("foo")


def test_schema_fv3_execution(fv3_fcstprop):
    d = {"executable": "fv3"}
    batchargs = {"batchargs": {"queue": "string", "walltime": "string"}}
    mpiargs = {"mpiargs": ["--flag1", "--flag2"]}
    threads = {"threads": 32}
    errors = fv3_fcstprop("execution")
    # Basic correctness:
    assert not errors(d)
    # batchargs may optionally be specified:
    assert not errors({**d, **batchargs})
    # mpiargs may be optionally specified:
    assert not errors({**d, **mpiargs})
    # threads may optionally be specified:
    assert not errors({**d, **threads})
    # All properties are ok:
    assert not errors({**d, **batchargs, **mpiargs, **threads})
    # Additional properties are not allowed:
    assert "Additional properties are not allowed" in errors(
        {**d, **mpiargs, **threads, "foo": "bar"}
    )


def test_schema_fv3_execution_batchargs(fv3_fcstprop):
    errors = fv3_fcstprop("execution", "properties", "batchargs")
    # Basic correctness, empty map is ok:
    assert not errors({})
    # Managed properties are fine:
    assert not errors({"queue": "string", "walltime": "string"})
    # But so are unknown ones:
    assert not errors({"--foo": 88})
    # It just has to be a map:
    assert "[] is not of type 'object'" in errors([])


def test_schema_fv3_execution_executable(fv3_fcstprop):
    errors = fv3_fcstprop("execution", "properties", "executable")
    # String value is ok:
    assert not errors("fv3.exe")
    # Anything else is not:
    assert "88 is not of type 'string'" in errors(88)


def test_schema_fv3_execution_mpiargs(fv3_fcstprop):
    errors = fv3_fcstprop("execution", "properties", "mpiargs")
    # Basic correctness:
    assert not errors(["string1", "string2"])
    # mpiargs may be empty:
    assert not errors([])
    # String values are expected:
    assert "88 is not of type 'string'" in errors(["string1", 88])


def test_schema_fv3_execution_threads(fv3_fcstprop):
    errors = fv3_fcstprop("execution", "properties", "threads")
    # threads must be non-negative, and an integer:
    assert not errors(0)
    assert not errors(4)
    assert "-1 is less than the minimum of 0" in errors(-1)
    assert "3.14 is not of type 'integer'" in errors(3.14)


def test_schema_fv3_field_table(fv3_fcstprop, fv3_field_table_vals):
    val, _ = fv3_field_table_vals
    base_file = {"base_file": "/some/path"}
    update_values = {"update_values": val}
    errors = fv3_fcstprop("field_table")
    # Just base_file is ok:
    assert not errors(base_file)
    # Just update_values is ok:
    assert not errors(update_values)
    # A combination of base_file and update_values is ok:
    assert not errors({**base_file, **update_values})
    # At least one is required:
    assert "is not valid" in errors({})


def test_schema_fv3_field_table_update_values(fv3_fcstprop, fv3_field_table_vals):
    val1, val2 = fv3_field_table_vals
    errors = fv3_fcstprop("field_table", "properties", "update_values")
    # A "fixed" profile-type entry is ok:
    assert not errors(val1)
    # A "profile" profile-type entry is ok:
    assert not errors(val2)
    # A combination of two valid entries is ok:
    assert not errors({**val1, **val2})
    # At least one entry is required:
    assert "does not have enough properties" in errors({})
    # longname is required:
    assert "'longname' is a required property" in errors(with_del(val1, "foo", "longname"))
    # longname must be a string:
    assert "88 is not of type 'string'" in errors(with_set(val1, 88, "foo", "longname"))
    # units is required:
    assert "'units' is a required property" in errors(with_del(val1, "foo", "units"))
    # units must be a string:
    assert "88 is not of type 'string'" in errors(with_set(val1, 88, "foo", "units"))
    # profile_type is required:
    assert "'profile_type' is a required property" in errors(with_del(val1, "foo", "profile_type"))
    # profile_type name has to be "fixed" or "profile":
    assert "'bogus' is not one of ['fixed', 'profile']" in errors(
        with_set(val1, "bogus", "foo", "profile_type", "name")
    )
    # surface_value is required:
    assert "'surface_value' is a required property" in errors(
        with_del(val1, "foo", "profile_type", "surface_value")
    )
    # surface_value is numeric:
    assert "'a string' is not of type 'number'" in errors(
        with_set(val1, "a string", "foo", "profile_type", "surface_value")
    )
    # top_value is required if name is "profile":
    assert "'top_value' is a required property" in errors(
        with_del(val2, "bar", "profile_type", "top_value")
    )
    # top_value is numeric:
    assert "'a string' is not of type 'number'" in errors(
        with_set(val2, "a string", "bar", "profile_type", "top_value")
    )


def test_schema_fv3_files_to_copy():
    test_schema_fv3_defs_filesToStage()


def test_schema_fv3_files_to_link():
    test_schema_fv3_defs_filesToStage()


def test_schema_fv3_lateral_boundary_conditions(fv3_fcstprop):
    d = {
        "interval_hours": 1,
        "offset": 0,
        "path": "/some/path",
    }
    errors = fv3_fcstprop("lateral_boundary_conditions")
    # Basic correctness:
    assert not errors(d)
    # All lateral_boundary_conditions items are required:
    assert "'interval_hours' is a required property" in errors(with_del(d, "interval_hours"))
    assert "'offset' is a required property" in errors(with_del(d, "offset"))
    assert "'path' is a required property" in errors(with_del(d, "path"))
    # interval_hours must be an integer of at least 1:
    assert "0 is less than the minimum of 1" in errors(with_set(d, 0, "interval_hours"))
    assert "'s' is not of type 'integer'" in errors(with_set(d, "s", "interval_hours"))
    # offset must be an integer of at least 0:
    assert "-1 is less than the minimum of 0" in errors(with_set(d, -1, "offset"))
    assert "'s' is not of type 'integer'" in errors(with_set(d, "s", "offset"))
    # path must be a string:
    assert "88 is not of type 'string'" in errors(with_set(d, 88, "path"))


def test_schema_fv3_length(fv3_fcstprop):
    errors = fv3_fcstprop("length")
    # Positive int is ok:
    assert not errors(6)
    # Zero is not ok:
    assert "0 is less than the minimum of 1" in errors(0)
    # A negative number is not ok:
    assert "-1 is less than the minimum of 1" in errors(-1)
    # Something other than an int is not ok:
    assert "'a string' is not of type 'integer'" in errors("a string")


def test_schema_fv3_model_configure(fv3_fcstprop):
    base_file = {"base_file": "/some/path"}
    update_values = {"update_values": {"foo": 88}}
    errors = fv3_fcstprop("model_configure")
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


def test_schema_fv3_model_configure_update_values(fv3_fcstprop):
    errors = fv3_fcstprop("model_configure", "properties", "update_values")
    # boolean, number, and string values are ok:
    assert not errors({"bool": True, "int": 88, "float": 3.14, "string": "foo"})
    # Other types are not, e.g.:
    assert "None is not of type 'boolean', 'number', 'string'" in errors({"null": None})
    # At least one entry is required:
    assert "does not have enough properties" in errors({})


def test_schema_fv3_namelist(fv3_fcstprop):
    base_file = {"base_file": "/some/path"}
    update_values = {"update_values": {"nml": {"var": "val"}}}
    errors = fv3_fcstprop("namelist")
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


def test_schema_fv3_namelist_update_values(fv3_fcstprop):
    errors = fv3_fcstprop("namelist", "properties", "update_values")
    # array, boolean, number, and string values are ok:
    assert not errors(
        {"nml": {"array": [1, 2, 3], "bool": True, "int": 88, "float": 3.14, "string": "foo"}}
    )
    # Other types are not, e.g.:
    assert "None is not of type 'array', 'boolean', 'number', 'string'" in errors(
        {"nml": {"null": None}}
    )
    # At least one namelist entry is required:
    assert "does not have enough properties" in errors({})
    # At least one val/var pair ir required:
    assert "does not have enough properties" in errors({"nml": {}})


def test_schema_fv3_run_dir(fv3_fcstprop):
    errors = fv3_fcstprop("run_dir")
    # Must be a string:
    assert not errors("/some/path")
    assert "88 is not of type 'string'" in errors(88)


# platform


def test_schema_platform():
    d = {"account": "me", "scheduler": "slurm"}
    errors = schema_validator("platform", "properties", "platform")
    # Basic correctness:
    assert not errors(d)
    # Extra top-level keys are forbidden:
    assert "Additional properties are not allowed" in errors(with_set(d, "bar", "foo"))
    # There is a fixed set of supported schedulers:
    assert "'foo' is not one of ['lsf', 'pbs', 'slurm']" in errors(with_set(d, "foo", "scheduler"))
    # account and scheduler are optional:
    assert not errors({})
    # account is required if scheduler is specified:
    assert "'account' is a dependency of 'scheduler'" in errors(with_del(d, "account"))
    # scheduler is required if account is specified:
    assert "'scheduler' is a dependency of 'account'" in errors(with_del(d, "scheduler"))


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


def test_schema_sfc_climo_gen(config):
    errors = schema_validator("sfc-climo-gen", "properties", "sfc_climo_gen")
    d = config["sfc_climo_gen"]
    # Basic correctness:
    assert not errors(d)
    # Additional properties are not allowed:
    assert "Additional properties are not allowed" in errors({**d, "foo": "bar"})


# def test_schema_sfc_climo_gen_namelist(config):
#     errors = schema_validator("sfc-climo-gen", "properties", "sfc_climo_gen", "properties", )
#     assert not errors(config["sfc_climo_gen"])
