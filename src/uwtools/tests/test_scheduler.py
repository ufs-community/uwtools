# pylint: disable=missing-function-docstring,redefined-outer-name
"""
Tests for uwtools.scheduler module.
"""

from pytest import fixture, raises

from uwtools.scheduler import JobScheduler

# LFS tests


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


def test_lsf_1(lsf_props):
    expected = """
#BSUB -P account_name
#BSUB -R affinity[core(1)]
#BSUB -R span[ptile=1]
#BSUB -W 00:01:00
#BSUB -n 1
#BSUB -q batch
""".strip()
    assert JobScheduler.get_scheduler(lsf_props).job_card.content() == expected


def test_lsf_2(lsf_props):
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


def test_lsf_3(lsf_props):
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


def test_lsf_4(lsf_props):
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


# PBS tests


@fixture
def pbs_props():
    return {
        "account": "account_name",
        "nodes": 1,
        "queue": "batch",
        "scheduler": "pbs",
        "tasks_per_node": 1,
        "walltime": "00:01:00",
    }


def test_pbs_1(pbs_props):
    expected = """
#PBS -A account_name
#PBS -l select=1:mpiprocs=1:ompthreads=1:ncpus=1
#PBS -l walltime=00:01:00
#PBS -q batch
""".strip()
    assert JobScheduler.get_scheduler(pbs_props).job_card.content() == expected


def test_pbs_2(pbs_props):
    pbs_props.update({"memory": "512M", "tasks_per_node": 4})
    expected = """
#PBS -A account_name
#PBS -l select=1:mpiprocs=4:ompthreads=1:ncpus=4:mem=512M
#PBS -l walltime=00:01:00
#PBS -q batch
""".strip()
    assert JobScheduler.get_scheduler(pbs_props).job_card.content() == expected


def test_pbs_3(pbs_props):
    pbs_props.update({"nodes": 3, "tasks_per_node": 4, "threads": 2})
    expected = """
#PBS -A account_name
#PBS -l select=3:mpiprocs=4:ompthreads=2:ncpus=8
#PBS -l walltime=00:01:00
#PBS -q batch
""".strip()
    assert JobScheduler.get_scheduler(pbs_props).job_card.content() == expected


def test_pbs_4(pbs_props):
    pbs_props.update({"memory": "512M", "nodes": 3, "tasks_per_node": 4, "threads": 2})
    expected = """
#PBS -A account_name
#PBS -l select=3:mpiprocs=4:ompthreads=2:ncpus=8:mem=512M
#PBS -l walltime=00:01:00
#PBS -q batch
""".strip()
    assert JobScheduler.get_scheduler(pbs_props).job_card.content() == expected


def test_pbs_5(pbs_props):
    pbs_props.update({"exclusive": "True"})
    expected = """
#PBS -A account_name
#PBS -l place=excl
#PBS -l select=1:mpiprocs=1:ompthreads=1:ncpus=1
#PBS -l walltime=00:01:00
#PBS -q batch
""".strip()
    assert JobScheduler.get_scheduler(pbs_props).job_card.content() == expected


def test_pbs_6(pbs_props):
    pbs_props.update({"exclusive": False, "placement": "vscatter"})
    expected = """
#PBS -A account_name
#PBS -l place=vscatter
#PBS -l select=1:mpiprocs=1:ompthreads=1:ncpus=1
#PBS -l walltime=00:01:00
#PBS -q batch
""".strip()
    assert JobScheduler.get_scheduler(pbs_props).job_card.content() == expected


def test_pbs_7(pbs_props):
    pbs_props.update({"exclusive": True, "placement": "vscatter"})
    expected = """
#PBS -A account_name
#PBS -l place=vscatter:excl
#PBS -l select=1:mpiprocs=1:ompthreads=1:ncpus=1
#PBS -l walltime=00:01:00
#PBS -q batch
""".strip()
    assert JobScheduler.get_scheduler(pbs_props).job_card.content() == expected


def test_pbs_8(pbs_props):
    pbs_props.update({"debug": "True"})
    expected = """
#PBS -A account_name
#PBS -l debug=true
#PBS -l select=1:mpiprocs=1:ompthreads=1:ncpus=1
#PBS -l walltime=00:01:00
#PBS -q batch
""".strip()
    assert JobScheduler.get_scheduler(pbs_props).job_card.content() == expected


# Slurm tests


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


def test_slurm_1(slurm_props):
    expected = """
#SBATCH --account=account_name
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --qos=batch
#SBATCH --time=00:01:00
""".strip()
    assert JobScheduler.get_scheduler(slurm_props).job_card.content() == expected


def test_slurm_2(slurm_props):
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


def test_slurm_3(slurm_props):
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


def test_slurm_4(slurm_props):
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


def test_slurm_5(slurm_props):
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


# Generic tests using PBS support.


def test_scheduler_bad_attr(pbs_props):
    js = JobScheduler.get_scheduler(pbs_props)
    with raises(AttributeError):
        assert js.bad_attr


def test_scheduler_bad_scheduler():
    with raises(KeyError) as e:
        JobScheduler.get_scheduler({"scheduler": "FOO"})
    assert "FOO is not a supported scheduler" in str(e.value)


def test_scheduler_dot_notation(pbs_props):
    js = JobScheduler.get_scheduler(pbs_props)
    assert js.account == "account_name"


def test_scheduler_prop_not_defined_raises_key_error(pbs_props):
    del pbs_props["scheduler"]
    with raises(KeyError) as e:
        JobScheduler.get_scheduler(pbs_props)
    assert "No scheduler defined in props" in str(e.value)


def test_scheduler_raises_exception_when_missing_required_attrs(pbs_props):
    del pbs_props["account"]
    with raises(ValueError) as e:
        JobScheduler.get_scheduler(pbs_props)
    assert "Missing required attributes: [account]" in str(e.value)
