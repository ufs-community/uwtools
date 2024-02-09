# pylint: disable=missing-function-docstring,protected-access,redefined-outer-name
"""
Tests for uwtools.scheduler module.
"""

import os
from pathlib import Path
from unittest.mock import patch

from pytest import fixture, raises

from uwtools import scheduler
from uwtools.exceptions import UWConfigError
from uwtools.scheduler import JobScheduler

# LSF tests

# PM sort all this to match scheduler module.


@fixture
def lsf_props():
    config = {
        "account": "account_name",
        "nodes": 1,
        "queue": "batch",
        "scheduler": "lsf",
        "tasks_per_node": 1,
        "threads": 1,
        "walltime": "00:01:00",
    }
    expected = [
        "#BSUB -P account_name",
        "#BSUB -R affinity[core(1)]",
        "#BSUB -R span[ptile=1]",
        "#BSUB -W 00:01:00",
        "#BSUB -n 1",
        "#BSUB -q batch",
    ]
    return config, expected


# def test_lsf_1(lsf_props):
#     lsf_config, expected_items = lsf_props
#     expected = "\n".join(expected_items)
#     assert JobScheduler.get_scheduler(lsf_config).runscript.content() == expected


# def test_lsf_2(lsf_props):
#     lsf_config, expected_items = lsf_props
#     lsf_config.update({"tasks_per_node": 12})
#     expected_items[2] = "#BSUB -R span[ptile=12]"
#     expected_items[4] = "#BSUB -n 12"
#     expected = "\n".join(expected_items)
#     assert JobScheduler.get_scheduler(lsf_config).runscript.content() == expected


# def test_lsf_3(lsf_props):
#     lsf_config, expected_items = lsf_props
#     lsf_config.update({"nodes": 2, "tasks_per_node": 6})
#     expected_items[2] = "#BSUB -R span[ptile=6]"
#     expected_items[4] = "#BSUB -n 12"
#     expected = "\n".join(expected_items)
#     assert JobScheduler.get_scheduler(lsf_config).runscript.content() == expected


# def test_lsf_4(lsf_props):
#     lsf_config, expected_items = lsf_props
#     lsf_config.update({"memory": "1MB", "nodes": 2, "tasks_per_node": 3, "threads": 2})
#     expected_items[1] = "#BSUB -R affinity[core(2)]"
#     expected_items[2] = "#BSUB -R span[ptile=3]"
#     expected_items[4] = "#BSUB -n 6"
#     new_items = [
#         "#BSUB -R rusage[mem=1000KB]",
#     ]
#     expected = "\n".join(sorted(expected_items + new_items))
#     assert JobScheduler.get_scheduler(lsf_config).runscript.content() == expected


# def test_lsf_5(lsf_props):
#     lsf_config, _ = lsf_props
#     expected = "bsub"
#     assert JobScheduler.get_scheduler(lsf_config)._submit_cmd == expected


# PBS tests


@fixture
def pbs_props():
    config = {
        "account": "account_name",
        "nodes": 1,
        "queue": "batch",
        "scheduler": "pbs",
        "tasks_per_node": 1,
        "walltime": "00:01:00",
    }
    expected = [
        "#PBS -A account_name",
        "#PBS -l select=1:mpiprocs=1:ompthreads=1:ncpus=1",
        "#PBS -l walltime=00:01:00",
        "#PBS -q batch",
    ]
    return config, expected


# def test_pbs_1(pbs_props):
#     pbs_config, expected_items = pbs_props
#     expected = "\n".join(expected_items)
#     assert JobScheduler.get_scheduler(pbs_config).runscript.content() == expected


# def test_pbs_2(pbs_props):
#     pbs_config, expected_items = pbs_props
#     pbs_config.update({"memory": "512M", "tasks_per_node": 4})
#     expected_items[1] = "#PBS -l select=1:mpiprocs=4:ompthreads=1:ncpus=4:mem=512M"
#     expected = "\n".join(expected_items)
#     assert JobScheduler.get_scheduler(pbs_config).runscript.content() == expected


# def test_pbs_3(pbs_props):
#     pbs_config, expected_items = pbs_props
#     pbs_config.update({"nodes": 3, "tasks_per_node": 4, "threads": 2})
#     expected_items[1] = "#PBS -l select=3:mpiprocs=4:ompthreads=2:ncpus=8"
#     expected = "\n".join(expected_items)
#     assert JobScheduler.get_scheduler(pbs_config).runscript.content() == expected


# def test_pbs_4(pbs_props):
#     pbs_config, expected_items = pbs_props
#     pbs_config.update({"memory": "512M", "nodes": 3, "tasks_per_node": 4, "threads": 2})
#     expected_items[1] = "#PBS -l select=3:mpiprocs=4:ompthreads=2:ncpus=8:mem=512M"
#     expected = "\n".join(expected_items)
#     assert JobScheduler.get_scheduler(pbs_config).runscript.content() == expected


# def test_pbs_5(pbs_props):
#     pbs_config, expected_items = pbs_props
#     pbs_config.update({"exclusive": "True"})
#     new_items = [
#         "#PBS -l place=excl",
#     ]
#     expected = "\n".join(sorted(expected_items + new_items))
#     assert JobScheduler.get_scheduler(pbs_config).runscript.content() == expected


# def test_pbs_6(pbs_props):
#     pbs_config, expected_items = pbs_props
#     pbs_config.update({"exclusive": False, "placement": "vscatter"})
#     new_items = [
#         "#PBS -l place=vscatter",
#     ]
#     expected = "\n".join(sorted(expected_items + new_items))
#     assert JobScheduler.get_scheduler(pbs_config).runscript.content() == expected


# def test_pbs_7(pbs_props):
#     pbs_config, expected_items = pbs_props
#     pbs_config.update({"exclusive": True, "placement": "vscatter"})
#     new_items = [
#         "#PBS -l place=vscatter:excl",
#     ]
#     expected = "\n".join(sorted(expected_items + new_items))
#     assert JobScheduler.get_scheduler(pbs_config).runscript.content() == expected


# def test_pbs_8(pbs_props):
#     pbs_config, expected_items = pbs_props
#     pbs_config.update({"debug": "True"})
#     new_items = [
#         "#PBS -l debug=true",
#     ]
#     expected = "\n".join(sorted(expected_items + new_items))
#     assert JobScheduler.get_scheduler(pbs_config).runscript.content() == expected


# def test_pbs_9(pbs_props):
#     pbs_config, _ = pbs_props
#     expected = "qsub"
#     assert JobScheduler.get_scheduler(pbs_config)._submit_cmd == expected


# Slurm tests


@fixture
def slurm_props():
    config = {
        "account": "account_name",
        "nodes": 1,
        "queue": "batch",
        "scheduler": "slurm",
        "tasks_per_node": 1,
        "walltime": "00:01:00",
    }
    expected = [
        "#SBATCH --account=account_name",
        "#SBATCH --nodes=1",
        "#SBATCH --ntasks-per-node=1",
        "#SBATCH --qos=batch",
        "#SBATCH --time=00:01:00",
    ]
    return config, expected


# def test_slurm_1(slurm_props):
#     slurm_config, expected_items = slurm_props
#     expected = "\n".join(expected_items)
#     assert JobScheduler.get_scheduler(slurm_config).runscript.content() == expected


# def test_slurm_2(slurm_props):
#     slurm_config, expected_items = slurm_props
#     slurm_config.update({"partition": "debug"})
#     new_items = [
#         "#SBATCH --partition=debug",
#     ]
#     expected = "\n".join(sorted(expected_items + new_items))
#     assert JobScheduler.get_scheduler(slurm_config).runscript.content() == expected


# def test_slurm_3(slurm_props):
#     slurm_config, expected_items = slurm_props
#     slurm_config.update({"tasks_per_node": 2, "threads": 4})
#     expected_items[2] = "#SBATCH --ntasks-per-node=2"
#     new_items = [
#         "#SBATCH --cpus-per-task=4",
#     ]
#     expected = "\n".join(sorted(expected_items + new_items))
#     assert JobScheduler.get_scheduler(slurm_config).runscript.content() == expected


# def test_slurm_4(slurm_props):
#     slurm_config, expected_items = slurm_props
#     slurm_config.update({"memory": "4MB", "tasks_per_node": 2})
#     expected_items[2] = "#SBATCH --ntasks-per-node=2"
#     new_items = [
#         "#SBATCH --mem=4MB",
#     ]
#     expected = "\n".join(sorted(expected_items + new_items))
#     assert JobScheduler.get_scheduler(slurm_config).runscript.content() == expected


# def test_slurm_5(slurm_props):
#     slurm_config, expected_items = slurm_props
#     slurm_config.update({"exclusive": "True"})
#     new_items = [
#         "#SBATCH --exclusive",
#     ]
#     expected = "\n".join(sorted(expected_items + new_items))
#     assert JobScheduler.get_scheduler(slurm_config).runscript.content() == expected


def test_slurm_6(slurm_props):
    slurm_config, _ = slurm_props
    expected = "sbatch"
    assert JobScheduler.get_scheduler(slurm_config)._submit_cmd == expected


# Generic tests using PBS support.


# def test_batchscript_dump(pbs_props, tmpdir):
#     outfile = tmpdir / "outfile.sh"
#     pbs_config, expected_items = pbs_props
#     bs = JobScheduler.get_scheduler(pbs_config).runscript
#     bs.dump(outfile)
#     reference = tmpdir / "reference.sh"
#     with open(reference, "w", encoding="utf-8") as f:
#         f.write("\n".join(["#!/bin/bash"] + expected_items))
#     assert compare_files(reference, outfile)


# def test_scheduler_bad_attr(pbs_props):
#     pbs_config, _ = pbs_props
#     js = JobScheduler.get_scheduler(pbs_config)
#     with raises(UWConfigError):
#         assert js.bad_attr


def test_scheduler_bad_scheduler():
    with raises(UWConfigError) as e:
        JobScheduler.get_scheduler({"scheduler": "FOO"})
    assert str(e.value).startswith("Scheduler 'FOO' should be one of: ")


def test_scheduler_dot_notation(pbs_props):
    pbs_config, _ = pbs_props
    js = JobScheduler.get_scheduler(pbs_config)
    assert js._props["account"] == "account_name"


def test_scheduler_prop_not_defined_raises_key_error(pbs_props):
    pbs_config, _ = pbs_props
    del pbs_config["scheduler"]
    with raises(UWConfigError) as e:
        JobScheduler.get_scheduler(pbs_config)
    assert str(e.value).startswith("No 'scheduler' defined in")


def test_scheduler_raises_exception_when_missing_required_attrs(pbs_props):
    pbs_config, _ = pbs_props
    del pbs_config["account"]
    with raises(UWConfigError) as e:
        JobScheduler.get_scheduler(pbs_config)
    assert "Missing required attributes: account" in str(e.value)


def test_scheduler_submit_job(pbs_props):
    pbs_config, _ = pbs_props
    js = JobScheduler.get_scheduler(pbs_config)
    outpath = Path("/path/to/batch/script")
    expected_command = f"{js._submit_cmd} {outpath}"
    with patch.object(scheduler, "execute") as execute:
        execute.return_value = (True, "")
        js.submit_job(outpath)
        execute.assert_called_once_with(cmd=expected_command, cwd=os.path.dirname(outpath))
