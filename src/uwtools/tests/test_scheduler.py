# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring
# pylint: disable=protected-access
# pylint: disable=redefined-outer-name
"""
Tests for uwtools.scheduler module.
"""

from typing import Any
from unittest.mock import patch

from pytest import fixture, raises

from uwtools import scheduler
from uwtools.exceptions import UWConfigError
from uwtools.scheduler import JobScheduler

# Fixtures

directive_separator = "="
managed_directives = {"account": lambda x: f"--a={x}", "walltime": lambda x: f"--t={x}"}
prefix = "#DIR"
submit_cmd = "sub"


@fixture
def props():
    return {"scheduler": "slurm", "walltime": "01:10:00", "account": "foo", "--pi": 3.14}


@fixture
def schedulerobj(props):
    return ConcreteScheduler(props=props)


@fixture
def lsf(props):
    return scheduler.LSF(props=props)


@fixture
def pbs(props):
    return scheduler.PBS(props=props)


@fixture
def slurm(props):
    return scheduler.Slurm(props=props)


class ConcreteScheduler(scheduler.JobScheduler):
    @property
    def _directive_separator(self) -> str:
        return directive_separator

    @property
    def _forbidden_directives(self) -> list[str]:
        return ["shell"]

    @property
    def _managed_directives(self) -> dict[str, Any]:
        return managed_directives

    @property
    def _prefix(self) -> str:
        return prefix

    @property
    def _submit_cmd(self) -> str:
        return submit_cmd


def test_JobScheduler(schedulerobj):
    assert isinstance(schedulerobj, JobScheduler)


def test_JobScheduler_directives(schedulerobj):
    assert schedulerobj.directives == ["#DIR --a=foo", "#DIR --pi=3.14", "#DIR --t=01:10:00"]


def test_JobScheduler_get_scheduler_fail_bad_directive_specified(props):
    scheduler = ConcreteScheduler.get_scheduler(props={**props, "shell": "csh"})
    with raises(UWConfigError) as e:
        assert scheduler.directives
    assert str(e.value).startswith("Directive 'shell' invalid for scheduler 'slurm'")


def test_JobScheduler_get_scheduler_fail_bad_scheduler_specified():
    with raises(UWConfigError) as e:
        ConcreteScheduler.get_scheduler(props={"scheduler": "foo"})
    assert str(e.value).startswith("Scheduler 'foo' should be one of:")


def test_JobScheduler_get_scheduler_fail_no_scheduler_specified():
    with raises(UWConfigError) as e:
        ConcreteScheduler.get_scheduler(props={})
    assert str(e.value).startswith("No 'scheduler' defined in")


def test_JobScheduler_get_scheduler_pass(props):
    assert isinstance(ConcreteScheduler.get_scheduler(props=props), scheduler.Slurm)


def test_JobScheduler_submit_job(schedulerobj, tmp_path):
    runscript = tmp_path / "runscript"
    submit_file = tmp_path / "runscript.submit"
    with patch.object(scheduler, "execute") as execute:
        execute.return_value = (True, None)
        assert schedulerobj.submit_job(runscript=runscript, submit_file=submit_file) is True
        execute.assert_called_once_with(
            cmd=f"sub {runscript} 2>&1 | tee {submit_file}", cwd=str(tmp_path)
        )


def test_JobScheduler__directive_separator(schedulerobj):
    assert schedulerobj._directive_separator == directive_separator


def test_JobScheduler__managed_directives(schedulerobj):
    assert schedulerobj._managed_directives == managed_directives


def test_JobScheduler__prefix(schedulerobj):
    assert schedulerobj._prefix == prefix


def test_JobScheduler__processed_props(props, schedulerobj):
    del props["scheduler"]
    assert schedulerobj._processed_props == props


def test_JobScheduler__submit_cmd(schedulerobj):
    assert schedulerobj._submit_cmd == submit_cmd


def test_JobScheduler__validate_props_no(schedulerobj):
    schedulerobj._props = {}
    with raises(UWConfigError) as e:
        schedulerobj._validate_props()
    assert str(e.value) == "Missing required directives: account, walltime"


def test_JobScheduler__validate_props_ok(schedulerobj):
    assert schedulerobj._validate_props() is None


def test_LSF(lsf):
    assert isinstance(lsf, JobScheduler)


def test_LSF__directive_separator(lsf):
    assert lsf._directive_separator == " "


def test_LSF__forbidden_directives(lsf):
    assert lsf._forbidden_directives == []


def test_LSF__managed_directives(lsf):
    mds = lsf._managed_directives
    assert mds["account"] == "-P"
    assert mds["jobname"] == "-J"
    assert mds["memory"]("1GB") == "-R rusage[mem=1GB]"
    assert mds["nodes"](2) == "-n 2"
    assert mds["queue"] == "-q"
    assert mds["shell"] == "-L"
    assert mds["stdout"] == "-o"
    assert mds["tasks_per_node"](4) == "-R span[ptile=4]"
    assert mds["threads"](8) == "-R affinity[core(8)]"
    assert mds["walltime"] == "-W"


def test_LSF__prefix(lsf):
    assert lsf._prefix == "#BSUB"


def test_LSF__processed_props(lsf):
    assert lsf._processed_props == {**lsf._props, "threads": 1}


def test_LSF__submit_cmd(lsf):
    assert lsf._submit_cmd == "bsub"


def test_PBS(pbs):
    assert isinstance(pbs, JobScheduler)


def test_PBS__directive_separator(pbs):
    assert pbs._directive_separator == " "


def test_PBS__forbidden_directives(pbs):
    assert pbs._forbidden_directives == []


def test_PBS__managed_directives(pbs):
    mds = pbs._managed_directives
    assert mds["account"] == "-A"
    assert mds["debug"](True) == "-l debug=true"
    assert mds["jobname"] == "-N"
    assert mds["memory"] == "mem"
    assert mds["nodes"](2) == "-l select=2"
    assert mds["queue"] == "-q"
    assert mds["shell"] == "-S"
    assert mds["stdout"] == "-o"
    assert mds["tasks_per_node"] == "mpiprocs"
    assert mds["threads"] == "ompthreads"
    assert mds["walltime"] == "-l walltime="


def test_PBS__placement(pbs):
    extras = {"placement": "foo", "exclusive": True}
    assert pbs._placement(items={**pbs._props, **extras})["-l place="] == "foo:excl"


def test_PBS__placement_no_op(pbs):
    assert pbs._placement(items=pbs._props) == pbs._props


def test_PBS__prefix(pbs):
    assert pbs._prefix == "#PBS"


def test_PBS__processed_props(pbs):
    assert pbs._processed_props == pbs._props


def test_PBS__select(pbs):
    expected = "2:mpiprocs=4:ompthreads=1:ncpus=4:mem=1GB"
    extras = {"nodes": 2, "tasks_per_node": 4, "memory": "1GB"}
    assert pbs._select(items={**pbs._props, **extras})["-l select="] == expected


def test_PBS__submit_cmd(pbs):
    assert pbs._submit_cmd == "qsub"


def test_Slurm(slurm):
    assert isinstance(slurm, JobScheduler)


def test_Slurm__directive_separator(slurm):
    assert slurm._directive_separator == "="


def test_Slurm__forbidden_directives(slurm):
    assert slurm._forbidden_directives == ["shell"]


def test_Slurm__managed_directives(slurm):
    mds = slurm._managed_directives
    assert mds["cores"] == "--ntasks"
    assert mds["debug"](True) == "--verbose"
    assert mds["debug"](False) is None
    assert mds["exclusive"](True) == "--exclusive"
    assert mds["exclusive"](False) is None
    assert mds["export"] == "--export"
    assert mds["jobname"] == "--job-name"
    assert mds["memory"] == "--mem"
    assert mds["nodes"] == "--nodes"
    assert mds["partition"] == "--partition"
    assert mds["queue"] == "--qos"
    assert mds["stderr"] == "--error"
    assert mds["stdout"] == "--output"
    assert mds["tasks_per_node"] == "--ntasks-per-node"
    assert mds["threads"] == "--cpus-per-task"
    assert mds["account"] == "--account"
    assert mds["walltime"] == "--time"


def test_Slurm__prefix(slurm):
    assert slurm._prefix == "#SBATCH"


def test_Slurm__processed_props(slurm):
    assert slurm._processed_props == slurm._props


def test_Slurm__submit_cmd(slurm):
    assert slurm._submit_cmd == "sbatch"
