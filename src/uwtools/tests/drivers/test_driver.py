# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring
# pylint: disable=protected-access
# pylint: disable=redefined-outer-name
"""
Tests for uwtools.drivers.driver module.
"""
import datetime as dt
import json
import logging
from pathlib import Path
from textwrap import dedent
from typing import Optional
from unittest.mock import Mock, PropertyMock, patch

import yaml
from iotaa import asset, task
from pytest import fixture, mark, raises

from uwtools.config.formats.yaml import YAMLConfig
from uwtools.drivers import driver
from uwtools.exceptions import UWConfigError
from uwtools.logging import log
from uwtools.scheduler import Slurm
from uwtools.tests.support import regex_logged

# Helpers


class Common:

    __test__ = False

    @task
    def atask(self):
        yield "atask"
        yield asset("atask", lambda: True)

    def provisioned_rundir(self):
        pass

    @classmethod
    def driver_name(cls) -> str:
        return "concrete"

    def _validate(self, schema_file: Optional[Path] = None) -> None:
        pass


class ConcreteAssetsCycleBased(Common, driver.AssetsCycleBased):
    pass


class ConcreteAssetsCycleLeadtimeBased(Common, driver.AssetsCycleLeadtimeBased):
    pass


class ConcreteAssetsTimeInvariant(Common, driver.AssetsTimeInvariant):
    pass


class ConcreteDriverCycleBased(Common, driver.DriverCycleBased):
    pass


class ConcreteDriverCycleLeadtimeBased(Common, driver.DriverCycleLeadtimeBased):
    pass


class ConcreteDriverTimeInvariant(Common, driver.DriverTimeInvariant):
    pass


def write(path, x):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(x, f)
        return path


# Fixtures


@fixture
def config(tmp_path):
    return {
        "concrete": {
            "base_file": str(write(tmp_path / "base.yaml", {"a": 11, "b": 22})),
            "execution": {
                "batchargs": {
                    "export": "NONE",
                    "nodes": 1,
                    "stdout": "{{ concrete.rundir }}/out",
                    "walltime": "00:05:00",
                },
                "executable": str(tmp_path / "qux"),
                "mpiargs": ["bar", "baz"],
                "mpicmd": "foo",
            },
            "rundir": str(tmp_path),
            "update_values": {"a": 33},
        },
        "platform": {
            "account": "me",
            "scheduler": "slurm",
        },
    }


@fixture
def controller_schema(tmp_path):
    return write(
        tmp_path / "concrete.jsonschema",
        {
            "properties": {
                "concrete": {
                    "properties": {
                        "execution": {"type": "object"},
                        "rundir": {"type": "string"},
                    },
                    "required": ["rundir"],
                    "type": "object",
                },
            },
            "required": ["concrete"],
            "type": "object",
        },
    )


@fixture
def assetsobj(config):
    return ConcreteAssetsTimeInvariant(config=config, dry_run=False)


@fixture
def driverobj(config):
    return ConcreteDriverTimeInvariant(config=config, dry_run=False, batch=True)


# Assets Tests


def test_Assets(assetsobj):
    assert Path(assetsobj.config["base_file"]).name == "base.yaml"


def test_Assets_fail_bad_config(config):
    with raises(UWConfigError) as e:
        ConcreteAssetsTimeInvariant(config=config["concrete"])
    assert str(e.value) == "Required 'concrete' block missing in config"


def test_Assets___repr___cycle_based(config):
    obj = ConcreteAssetsCycleBased(config=config, cycle=dt.datetime(2024, 7, 2, 12))
    expected = "concrete 2024-07-02T12:00 in %s" % obj.config["rundir"]
    assert repr(obj) == expected


def test_Assets___repr___cycle_and_leadtime_based(config):
    obj = ConcreteAssetsCycleLeadtimeBased(
        config=config, cycle=dt.datetime(2024, 7, 2, 12), leadtime=dt.timedelta(hours=6)
    )
    expected = "concrete 2024-07-02T12:00 06:00:00 in %s" % obj.config["rundir"]
    assert repr(obj) == expected


def test_Assets___repr___time_invariant(config):
    obj = ConcreteAssetsTimeInvariant(config=config)
    expected = "concrete in %s" % obj.config["rundir"]
    assert repr(obj) == expected


def test_Assets___str__(assetsobj):
    assert str(assetsobj) == "concrete"


def test_Assets_config(assetsobj):
    # The user-accessible object is equivalent to the internal driver config:
    assert assetsobj.config == assetsobj._config
    # But they are separate objects:
    assert not assetsobj.config is assetsobj._config


def test_Assets_config_full(assetsobj):
    # The user-accessible object is equivalent to the internal driver config:
    assert assetsobj.config_full == assetsobj._config_full
    # But they are separate objects:
    assert not assetsobj.config_full is assetsobj._config_full


def test_Assets_controller(config, controller_schema):
    config["controller"] = {"rundir": "/controller/run/dir"}
    del config["concrete"]["rundir"]
    with patch.object(ConcreteAssetsTimeInvariant, "_validate", driver.Assets._validate):
        with raises(UWConfigError):
            ConcreteAssetsTimeInvariant(config=config, schema_file=controller_schema)
        assert ConcreteAssetsTimeInvariant(
            config=config, schema_file=controller_schema, controller="controller"
        )


def test_Assets_cycle(config):
    cycle = dt.datetime(2024, 7, 2, 12)
    obj = ConcreteAssetsCycleBased(config=config, cycle=cycle)
    assert obj.cycle == cycle


@mark.parametrize("val", (True, False))
def test_Assets_dry_run(config, val):
    with patch.object(driver, "dryrun") as dryrun:
        ConcreteAssetsTimeInvariant(config=config, dry_run=val)
        dryrun.assert_called_once_with(enable=val)


def test_Assets_key_path(config, tmp_path):
    config_file = tmp_path / "config.yaml"
    config_file.write_text(yaml.dump({"foo": {"bar": config}}))
    assetsobj = ConcreteAssetsTimeInvariant(
        config=config_file, dry_run=False, key_path=["foo", "bar"]
    )
    assert assetsobj.config == config[assetsobj.driver_name()]


def test_Assets_leadtime(config):
    cycle = dt.datetime(2024, 7, 2, 12)
    leadtime = dt.timedelta(hours=6)
    obj = ConcreteAssetsCycleLeadtimeBased(config=config, cycle=cycle, leadtime=leadtime)
    assert obj.cycle == cycle
    assert obj.leadtime == leadtime


def test_Assets_validate(assetsobj, caplog):
    log.setLevel(logging.INFO)
    assetsobj.validate()
    assert regex_logged(caplog, "State: Ready")


def test_Assets_validate_key_path(config, controller_schema):
    config = {"a": {"b": config}}
    with patch.object(ConcreteAssetsTimeInvariant, "_validate", driver.Assets._validate):
        assert ConcreteAssetsTimeInvariant(
            config=config, key_path=["a", "b"], schema_file=controller_schema
        )


@mark.parametrize(
    "base_file,update_values,expected",
    [
        (False, False, {}),
        (False, True, {"a": 33}),
        (True, False, {"a": 11, "b": 22}),
        (True, True, {"a": 33, "b": 22}),
    ],
)
def test_Assets__create_user_updated_config_base_file(
    assetsobj, base_file, expected, tmp_path, update_values
):
    path = tmp_path / "updated.yaml"
    dc = assetsobj.config
    if not base_file:
        del dc["base_file"]
    if not update_values:
        del dc["update_values"]
    ConcreteAssetsTimeInvariant._create_user_updated_config(
        config_class=YAMLConfig, config_values=dc, path=path
    )
    with open(path, "r", encoding="utf-8") as f:
        updated = yaml.safe_load(f)
    assert updated == expected


def test_Assets__rundir(assetsobj):
    assert assetsobj.rundir == Path(assetsobj.config["rundir"])


def test_Assets__schema_name():
    with patch.object(driver.Assets, "driver_name", return_value="a_driver"):
        assert driver.Assets._schema_name() == "a-driver"


def test_Assets__validate_internal(assetsobj):
    with patch.object(assetsobj, "_validate", driver.Assets._validate):
        with patch.object(driver, "validate_internal") as validate_internal:
            assetsobj._validate(assetsobj)
        assert validate_internal.call_args_list[0].kwargs == {
            "schema_name": "concrete",
            "config": assetsobj.config_full,
        }


def test_Assets__validate_external(config):
    schema_file = Path("/path/to/jsonschema")
    with patch.object(ConcreteAssetsTimeInvariant, "_validate", driver.Assets._validate):
        with patch.object(driver, "validate_external") as validate_external:
            assetsobj = ConcreteAssetsTimeInvariant(schema_file=schema_file, config=config)
        assert validate_external.call_args_list[0].kwargs == {
            "schema_file": schema_file,
            "config": assetsobj.config_full,
        }


# Driver Tests


def test_Driver(driverobj):
    assert Path(driverobj.config["base_file"]).name == "base.yaml"
    assert driverobj._batch is True


def test_Driver_cycle(config):
    cycle = dt.datetime(2024, 7, 2, 12)
    obj = ConcreteDriverCycleBased(config=config, cycle=cycle)
    assert obj.cycle == cycle


def test_Driver_controller(config, controller_schema):
    config["controller"] = {
        "execution": {"executable": "/path/to/coupled.exe"},
        "rundir": "/controller/run/dir",
    }
    del config["concrete"]["rundir"]
    del config["concrete"]["execution"]
    with patch.object(ConcreteDriverTimeInvariant, "_validate", driver.Driver._validate):
        with raises(UWConfigError):
            ConcreteDriverTimeInvariant(config=config, schema_file=controller_schema)
        assert ConcreteDriverTimeInvariant(
            config=config, schema_file=controller_schema, controller="controller"
        )


def test_Driver_leadtime(config):
    cycle = dt.datetime(2024, 7, 2, 12)
    leadtime = dt.timedelta(hours=6)
    obj = ConcreteDriverCycleLeadtimeBased(config=config, cycle=cycle, leadtime=leadtime)
    assert obj.cycle == cycle
    assert obj.leadtime == leadtime


@mark.parametrize("batch", [True, False])
def test_Driver_run(batch, driverobj):
    driverobj._batch = batch
    executable = Path(driverobj.config["execution"]["executable"])
    executable.touch()
    with patch.object(driverobj, "_run_via_batch_submission") as rvbs:
        with patch.object(driverobj, "_run_via_local_execution") as rvle:
            driverobj.run()
        if batch:
            rvbs.assert_called_once_with()
            rvle.assert_not_called()
        else:
            rvbs.assert_not_called()
            rvle.assert_called_once_with()


@mark.parametrize(
    "arg,type_", [("envcmds", list), ("envvars", dict), ("execution", list), ("scheduler", Slurm)]
)
def test_Driver_runscript(arg, driverobj, type_):
    with patch.object(driverobj, "_runscript") as runscript:
        driverobj.runscript()
        runscript.assert_called_once()
        assert isinstance(runscript.call_args.kwargs[arg], type_)


def test_Driver__run_via_batch_submission(driverobj):
    runscript = driverobj._runscript_path
    executable = Path(driverobj.config["execution"]["executable"])
    executable.touch()
    with patch.object(driverobj, "provisioned_rundir") as prd:
        with patch.object(
            ConcreteDriverTimeInvariant, "_scheduler", new_callable=PropertyMock
        ) as scheduler:
            driverobj._run_via_batch_submission()
            scheduler().submit_job.assert_called_once_with(
                runscript=runscript, submit_file=Path(f"{runscript}.submit")
            )
        prd.assert_called_once_with()


def test_Driver__run_via_local_execution(driverobj):
    executable = Path(driverobj.config["execution"]["executable"])
    executable.touch()
    with patch.object(driverobj, "provisioned_rundir") as prd:
        with patch.object(driver, "run_shell_cmd") as run_shell_cmd:
            driverobj._run_via_local_execution()
            run_shell_cmd.assert_called_once_with(
                cmd="{x} >{x}.out 2>&1".format(x=driverobj._runscript_path),
                cwd=driverobj.rundir,
                log_output=True,
            )
        prd.assert_called_once_with()


@mark.parametrize(
    "base_file,update_values,expected",
    [
        (False, False, {}),
        (False, True, {"a": 33}),
        (True, False, {"a": 11, "b": 22}),
        (True, True, {"a": 33, "b": 22}),
    ],
)
def test_Driver__create_user_updated_config_base_file(
    base_file, driverobj, expected, tmp_path, update_values
):
    path = tmp_path / "updated.yaml"
    if not base_file:
        del driverobj._config["base_file"]
    if not update_values:
        del driverobj._config["update_values"]
    ConcreteDriverTimeInvariant._create_user_updated_config(
        config_class=YAMLConfig, config_values=driverobj.config, path=path
    )
    with open(path, "r", encoding="utf-8") as f:
        updated = yaml.safe_load(f)
    assert updated == expected


def test_Driver__namelist_schema_custom(driverobj, tmp_path):
    nmlschema = {"properties": {"n": {"type": "integer"}}, "type": "object"}
    schema = {"foo": {"bar": nmlschema}}
    schema_path = tmp_path / "test.jsonschema"
    with open(schema_path, "w", encoding="utf-8") as f:
        json.dump(schema, f)
    with patch.object(ConcreteDriverTimeInvariant, "config", new_callable=PropertyMock) as dc:
        dc.return_value = {"baz": {"qux": {"validate": True}}}
        with patch.object(driver, "get_schema_file", return_value=schema_path):
            assert (
                driverobj._namelist_schema(config_keys=["baz", "qux"], schema_keys=["foo", "bar"])
                == nmlschema
            )


def test_Driver__namelist_schema_default(driverobj, tmp_path):
    nmlschema = {"properties": {"n": {"type": "integer"}}, "type": "object"}
    schema = {
        "properties": {
            "concrete": {"properties": {"namelist": {"properties": {"update_values": nmlschema}}}}
        }
    }
    schema_path = tmp_path / "test.jsonschema"
    with open(schema_path, "w", encoding="utf-8") as f:
        json.dump(schema, f)
    with patch.object(ConcreteDriverTimeInvariant, "config", new_callable=PropertyMock) as dc:
        dc.return_value = {"namelist": {"validate": True}}
        with patch.object(driver, "get_schema_file", return_value=schema_path):
            assert driverobj._namelist_schema() == nmlschema


def test_Driver__namelist_schema_default_disable(driverobj):
    with patch.object(ConcreteDriverTimeInvariant, "config", new_callable=PropertyMock) as dc:
        dc.return_value = {"namelist": {"validate": False}}
        assert driverobj._namelist_schema() == {"type": "object"}


def test_Driver__run_resources_fail(driverobj):
    del driverobj._config_intermediate["platform"]
    with raises(UWConfigError) as e:
        assert driverobj._run_resources
    assert str(e.value) == "Required 'platform' block missing in config"


def test_Driver__run_resources_pass(driverobj):
    account = "me"
    scheduler = "slurm"
    walltime = "00:05:00"
    driverobj._config["execution"].update({"batchargs": {"threads": 4, "walltime": walltime}})
    assert driverobj._run_resources == {
        "account": account,
        "rundir": driverobj.rundir,
        "scheduler": scheduler,
        "stdout": "runscript.concrete.out",
        "threads": 4,
        "walltime": walltime,
    }


def test_Driver__runcmd(driverobj):
    executable = driverobj.config["execution"]["executable"]
    assert driverobj._runcmd == f"foo bar baz {executable}"


def test_Driver__runscript(driverobj):
    expected = """
    #!/bin/bash

    #DIR --d1
    #DIR --d2

    cmd1
    cmd2

    export VAR1=1
    export VAR2=2

    foo
    bar
    """
    scheduler = Mock(directives=["#DIR --d1", "#DIR --d2"])
    assert (
        driverobj._runscript(
            execution=["foo", "bar"],
            envcmds=["cmd1", "cmd2"],
            envvars={"VAR1": 1, "VAR2": 2},
            scheduler=scheduler,
        )
        == dedent(expected).strip()
    )


def test_Driver__runscript_execution_only(driverobj):
    expected = """
    #!/bin/bash

    foo
    bar
    """
    assert driverobj._runscript(execution=["foo", "bar"]) == dedent(expected).strip()


def test_Driver__runscript_done_file(driverobj):
    assert driverobj._runscript_done_file == "runscript.concrete.done"


def test_Driver__runscript_path(driverobj):
    rundir = Path(driverobj.config["rundir"])
    assert driverobj._runscript_path == rundir / "runscript.concrete"


def test_Driver__scheduler(driverobj):
    with patch.object(driver, "JobScheduler") as JobScheduler:
        scheduler = JobScheduler.get_scheduler()
        assert driverobj._scheduler == scheduler
        JobScheduler.get_scheduler.assert_called_with(driverobj._run_resources)


def test_Driver__validate_internal(assetsobj):
    with patch.object(assetsobj, "_validate", driver.Driver._validate):
        with patch.object(driver, "validate_internal") as validate_internal:
            assetsobj._validate(assetsobj)
        assert validate_internal.call_args_list[0].kwargs == {
            "schema_name": "concrete",
            "config": assetsobj.config_full,
        }
        assert validate_internal.call_args_list[1].kwargs == {
            "schema_name": "platform",
            "config": assetsobj.config_full,
        }


def test_Driver__validate_external(config):
    schema_file = Path("/path/to/jsonschema")
    with patch.object(ConcreteAssetsTimeInvariant, "_validate", driver.Driver._validate):
        with patch.object(driver, "validate_external") as validate_external:
            assetsobj = ConcreteAssetsTimeInvariant(schema_file=schema_file, config=config)
        assert validate_external.call_args_list[0].kwargs == {
            "schema_file": schema_file,
            "config": assetsobj.config_full,
        }


def test_Driver__write_runscript(driverobj):
    rundir = driverobj.config["rundir"]
    path = Path(rundir, "runscript")
    executable = driverobj.config["execution"]["executable"]
    driverobj._write_runscript(path=path, envvars={"FOO": "bar", "BAZ": "qux"})
    expected = f"""
    #!/bin/bash

    #SBATCH --account=me
    #SBATCH --chdir={rundir}
    #SBATCH --export=NONE
    #SBATCH --nodes=1
    #SBATCH --output={rundir}/out
    #SBATCH --time=00:05:00

    export FOO=bar
    export BAZ=qux

    time foo bar baz {executable}
    test $? -eq 0 && touch runscript.concrete.done
    """
    with open(path, "r", encoding="utf-8") as f:
        actual = f.read()
    assert actual.strip() == dedent(expected).strip()


def test_Driver__write_runscript_threads_fail(driverobj):
    path = Path(driverobj.config["rundir"], "runscript")
    driverobj._config["execution"]["threads"] = 4
    with raises(UWConfigError) as e:
        driverobj._write_runscript(path=path)
    assert str(e.value) == "Config specified threads but driver does not set OMP_NUM_THREADS"


def test__add_docstring():
    class C:
        pass

    assert getattr(C, "__doc__") is None
    with patch.object(driver, "C", C, create=True):
        class_ = driver.C  # type: ignore # pylint: disable=no-member
        omit = [
            "batch",
            "config",
            "controller",
            "cycle",
            "dry_run",
            "key_path",
            "leadtime",
            "schema_file",
        ]
        driver._add_docstring(class_=class_, omit=omit)
    assert getattr(C, "__doc__").strip() == "A driver."
