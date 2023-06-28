# pylint: disable=missing-function-docstring,redefined-outer-name

import pathlib

import pytest
from pytest import fixture

from uwtools import config
from uwtools.scheduler import JobScheduler


@pytest.mark.skip()
def test_scheduler_dot_notation():
    props = config.YAMLConfig(pathlib.Path("tests/fixtures/simple2.yaml"))

    js = JobScheduler.get_scheduler(props)
    expected = "user_account"
    actual = js.account

    assert actual == expected


@pytest.mark.skip()
def test_scheduler_prop_not_defined_raises_key_error():
    with pytest.raises(KeyError) as error:
        props = {
            "account": "user_account",
            "queue": "batch",
            "walltime": "00:01:00",
            "tasks_per_node": 1,
            "extra_stuff": "12345",
            "nodes": 1,
        }

        JobScheduler.get_scheduler(props)
    expected = "no scheduler defined in props: [account, queue, walltime, tasks_per_node"
    actual = str(error.value)
    assert expected in actual


@pytest.mark.skip()
def test_scheduler_raises_exception_when_missing_required_attribs():
    with pytest.raises(ValueError) as error:
        props = {
            "scheduler": "pbs",
            "queue": "batch",
            "walltime": "00:01:00",
            "nodes": 1,
            "tasks_per_node": 1,
            "debug": True,
        }

        JobScheduler.get_scheduler(props)
    expected = "missing required attributes: [account]"
    actual = str(error.value)
    assert expected in actual


@pytest.mark.skip()
def test_pbs1():
    expected = """#PBS -A account_name
#PBS -q batch
#PBS -l walltime=00:01:00
#PBS -l select=1:mpiprocs=1:ompthreads=1:ncpus=1"""

    props = {
        "scheduler": "pbs",
        "account": "account_name",
        "queue": "batch",
        "walltime": "00:01:00",
        "nodes": 1,
        "tasks_per_node": 1,
    }

    js = JobScheduler.get_scheduler(props)
    actual = js.job_card.content()

    assert actual == expected


@pytest.mark.skip()
def test_pbs2():
    expected = """#PBS -A account_name
#PBS -q batch
#PBS -l walltime=00:01:00
#PBS -l select=1:mpiprocs=4:ompthreads=1:ncpus=4:mem=512M"""

    props = {
        "scheduler": "pbs",
        "account": "account_name",
        "queue": "batch",
        "walltime": "00:01:00",
        "nodes": 1,
        "tasks_per_node": 4,
        "memory": "512M",
    }

    js = JobScheduler.get_scheduler(props)
    actual = js.job_card.content()

    assert actual == expected


@pytest.mark.skip()
def test_pbs3():
    expected = """#PBS -A account_name
#PBS -q batch
#PBS -l walltime=00:01:00
#PBS -l select=3:mpiprocs=4:ompthreads=2:ncpus=8"""

    props = {
        "scheduler": "pbs",
        "account": "account_name",
        "queue": "batch",
        "walltime": "00:01:00",
        "nodes": 3,
        "tasks_per_node": 4,
        "threads": 2,
    }

    js = JobScheduler.get_scheduler(props)
    actual = js.job_card.content()

    assert actual == expected


@pytest.mark.skip()
def test_pbs4():
    expected = """#PBS -A account_name
#PBS -q batch
#PBS -l walltime=00:01:00
#PBS -l select=3:mpiprocs=4:ompthreads=2:ncpus=8:mem=512M"""

    props = {
        "scheduler": "pbs",
        "account": "account_name",
        "queue": "batch",
        "walltime": "00:01:00",
        "nodes": 3,
        "tasks_per_node": 4,
        "threads": 2,
        "memory": "512M",
    }

    js = JobScheduler.get_scheduler(props)
    actual = js.job_card.content()

    assert actual == expected


@pytest.mark.skip()
def test_pbs5():
    expected = """#PBS -A account_name
#PBS -q batch
#PBS -l walltime=00:01:00
#PBS -l select=1:mpiprocs=1:ompthreads=1:ncpus=1
#PBS -l place=excl"""

    props = {
        "scheduler": "pbs",
        "account": "account_name",
        "queue": "batch",
        "walltime": "00:01:00",
        "nodes": 1,
        "tasks_per_node": 1,
        "exclusive": True,
    }

    js = JobScheduler.get_scheduler(props)
    actual = js.job_card.content()

    assert actual == expected


@pytest.mark.skip()
def test_pbs6():
    expected = """#PBS -A account_name
#PBS -q batch
#PBS -l walltime=00:01:00
#PBS -l select=1:mpiprocs=1:ompthreads=1:ncpus=1
#PBS -l place=vscatter"""

    props = {
        "scheduler": "pbs",
        "account": "account_name",
        "queue": "batch",
        "walltime": "00:01:00",
        "nodes": 1,
        "tasks_per_node": 1,
        "exclusive": False,
        "placement": "vscatter",
    }

    js = JobScheduler.get_scheduler(props)
    actual = js.job_card.content()

    assert actual == expected


@pytest.mark.skip()
def test_pbs7():
    expected = """#PBS -A account_name
#PBS -q batch
#PBS -l walltime=00:01:00
#PBS -l select=1:mpiprocs=1:ompthreads=1:ncpus=1
#PBS -l place=vscatter:excl"""

    props = {
        "scheduler": "pbs",
        "account": "account_name",
        "queue": "batch",
        "walltime": "00:01:00",
        "nodes": 1,
        "tasks_per_node": 1,
        "exclusive": True,
        "placement": "vscatter",
    }

    js = JobScheduler.get_scheduler(props)
    actual = js.job_card.content()

    assert actual == expected


@pytest.mark.skip()
def test_pbs8():
    expected = """#PBS -A account_name
#PBS -q batch
#PBS -l walltime=00:01:00
#PBS -l debug=true
#PBS -l select=1:mpiprocs=1:ompthreads=1:ncpus=1"""

    props = {
        "scheduler": "pbs",
        "account": "account_name",
        "queue": "batch",
        "walltime": "00:01:00",
        "nodes": 1,
        "tasks_per_node": 1,
        "debug": True,
    }

    js = JobScheduler.get_scheduler(props)
    actual = js.job_card.content()

    assert actual == expected


@fixture
def slurm_props():
    return {
        "account": "account_name",
        "nodes": 1,
        "queue": "batch",
        "scheduler": "slurm",
        "tasks_per_node": 1,
        "walltime": "00:01:00",
    }


def test_slurm1(slurm_props):
    expected = """
#SBATCH --account=account_name
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --qos=batch
#SBATCH --time=00:01:00
""".strip()
    assert JobScheduler.get_scheduler(slurm_props).job_card.content() == expected


def test_slurm2(slurm_props):
    slurm_props.update({"partition": "debug"})
    expected = """
#SBATCH --account=account_name
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --partition=debug
#SBATCH --qos=batch
#SBATCH --time=00:01:00
""".strip()
    assert JobScheduler.get_scheduler(slurm_props).job_card.content() == expected


def test_slurm3(slurm_props):
    slurm_props.update({"tasks_per_node": 2, "threads": 4})
    expected = """
#SBATCH --account=account_name
#SBATCH --cpus-per-task=4
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=2
#SBATCH --qos=batch
#SBATCH --time=00:01:00
""".strip()
    assert JobScheduler.get_scheduler(slurm_props).job_card.content() == expected


def test_slurm4(slurm_props):
    slurm_props.update({"memory": "4MB", "tasks_per_node": 2})
    expected = """
#SBATCH --account=account_name
#SBATCH --mem=4MB
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=2
#SBATCH --qos=batch
#SBATCH --time=00:01:00
""".strip()
    assert JobScheduler.get_scheduler(slurm_props).job_card.content() == expected


def test_slurm5(slurm_props):
    slurm_props.update({"exclusive": "True"})
    expected = """
#SBATCH --account=account_name
#SBATCH --exclusive=True
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --qos=batch
#SBATCH --time=00:01:00
""".strip()
    assert JobScheduler.get_scheduler(slurm_props).job_card.content() == expected


@fixture
def lsf_props():
    return {
        "account": "account_name",
        "nodes": 1,
        "queue": "batch",
        "scheduler": "lsf",
        "tasks_per_node": 1,
        "threads": 1,
        "walltime": "00:01:00",
    }


def test_lsf1(lsf_props):
    expected = """
#BSUB -P account_name
#BSUB -R affinity[core(1)]
#BSUB -R span[ptile=1]
#BSUB -W 00:01:00
#BSUB -n 1
#BSUB -q batch
""".strip()
    assert JobScheduler.get_scheduler(lsf_props).job_card.content() == expected


def test_lsf2(lsf_props):
    lsf_props.update({"tasks_per_node": 12})
    expected = """
#BSUB -P account_name
#BSUB -R affinity[core(1)]
#BSUB -R span[ptile=12]
#BSUB -W 00:01:00
#BSUB -n 12
#BSUB -q batch
""".strip()
    assert JobScheduler.get_scheduler(lsf_props).job_card.content() == expected


def test_lsf3(lsf_props):
    lsf_props.update({"nodes": 2, "tasks_per_node": 6})
    expected = """
#BSUB -P account_name
#BSUB -R affinity[core(1)]
#BSUB -R span[ptile=6]
#BSUB -W 00:01:00
#BSUB -n 12
#BSUB -q batch
""".strip()
    assert JobScheduler.get_scheduler(lsf_props).job_card.content() == expected


def test_lsf4(lsf_props):
    lsf_props.update({"memory": "1MB", "nodes": 2, "tasks_per_node": 3, "threads": 2})
    job_card = JobScheduler.get_scheduler(lsf_props).job_card
    expected = """
#BSUB -P account_name
#BSUB -R affinity[core(2)]
#BSUB -R rusage[mem=1000KB]
#BSUB -R span[ptile=3]
#BSUB -W 00:01:00
#BSUB -n 6
#BSUB -q batch
""".strip()
    assert job_card.content() == expected
    assert str(job_card) == expected
