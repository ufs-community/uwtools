# pylint: disable=all
import pytest

from uwtools.scheduler import JobScheduler


def test_scheduler_slurm():

    expected = """#SBATCH --account=user_account
#SBATCH --qos=batch
#SBATCH --time=00:01:00
#SBATCH --ntasks-per-node=1
#SBATCH --nodes=1
#SBATCH extra_stuff=12345"""

    props = {
        "account": "user_account",
        "scheduler": "slurm",
        "queue": "batch",
        "walltime": "00:01:00",
        "tasks_per_node": 1,
        "extra_stuff": "12345",
        "nodes": 1,
    }

    js = JobScheduler.get_scheduler(props)
    actual = js.job_card.content()

    assert actual == expected


def test_scheduler_lsf():

    expected = """#BSUB -P user_account
#BSUB -q batch
#BSUB -W 00:01:00
#BSUB -n 1
#BSUB extra_stuff 12345"""

    props = {
        "account": "user_account",
        "scheduler": "lsf",
        "queue": "batch",
        "walltime": "00:01:00",
        "tasks_per_node": 1,
        "extra_stuff": "12345",
        "nodes": 1,
    }

    js = JobScheduler.get_scheduler(props)
    actual = js.job_card.content()

    assert actual == expected


def test_scheduler_pbs():

    expected = """#PBS -A user_account
#PBS -q batch
#PBS -l walltime=00:01:00
#PBS extra_stuff 12345
#PBS -l select=1:mpiprocs=1"""

    props = {
        "account": "user_account",
        "scheduler": "pbs",
        "queue": "batch",
        "walltime": "00:01:00",
        "tasks_per_node": 1,
        "extra_stuff": "12345",
        "nodes": 1,
    }

    js = JobScheduler.get_scheduler(props)
    actual = js.job_card.content()

    assert actual == expected


def test_scheduler_dot_notation():

    props = {
        "account": "user_account",
        "scheduler": "lsf",
        "queue": "batch",
        "walltime": "00:01:00",
        "tasks_per_node": 1,
        "extra_stuff": "12345",
        "nodes": 1,
    }

    js = JobScheduler.get_scheduler(props)
    expected = "user_account"
    actual = js.account

    assert actual == expected


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
    expected = (
        "no scheduler defined in props: [account, queue, walltime, tasks_per_node"
    )
    actual = str(error.value)
    assert expected in actual


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


def test_pbs1():
    expected = """#PBS -A account_name
#PBS -q batch
#PBS -l walltime=00:01:00
#PBS -l select=1:mpiprocs=1"""

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


def test_pbs2():
    expected = """#PBS -A account_name
#PBS -q batch
#PBS -l walltime=00:01:00
#PBS -l select=1:mpiprocs=4:mem=512M"""

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


def test_pbs5():
    expected = """#PBS -A account_name
#PBS -q batch
#PBS -l walltime=00:01:00
#PBS -l select=1:mpiprocs=1
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


def test_pbs6():
    expected = """#PBS -A account_name
#PBS -q batch
#PBS -l walltime=00:01:00
#PBS -l select=1:mpiprocs=1
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


def test_pbs7():
    expected = """#PBS -A account_name
#PBS -q batch
#PBS -l walltime=00:01:00
#PBS -l select=1:mpiprocs=1
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


def test_pbs8():
    expected = """#PBS -A account_name
#PBS -q batch
#PBS -l walltime=00:01:00
#PBS -l debug=True
#PBS -l select=1:mpiprocs=1"""

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

    print(actual)
    print("****")
    print(expected)
    assert actual == expected


def test_slurm1():
    expected = """#SBATCH --account=account_name
#SBATCH --qos=batch
#SBATCH --time=00:01:00
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1"""

    props = {
        "scheduler": "slurm",
        "account": "account_name",
        "queue": "batch",
        "walltime": "00:01:00",
        "nodes": 1,
        "tasks_per_node": 1,
    }

    js = JobScheduler.get_scheduler(props)
    actual = js.job_card.content()

    assert actual == expected


def test_slurm2():
    expected = """#SBATCH --account=account_name
#SBATCH --qos=batch
#SBATCH --partition=debug
#SBATCH --time=00:01:00
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1"""

    props = {
        "scheduler": "slurm",
        "account": "account_name",
        "queue": "batch",
        "partition": "debug",
        "walltime": "00:01:00",
        "nodes": 1,
        "tasks_per_node": 1,
    }

    js = JobScheduler.get_scheduler(props)
    actual = js.job_card.content()

    assert actual == expected


def test_slurm3():
    expected = """#SBATCH --account=account_name
#SBATCH --qos=batch
#SBATCH --time=00:01:00
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=2
#SBATCH --cpus-per-task=4"""

    props = {
        "scheduler": "slurm",
        "account": "account_name",
        "queue": "batch",
        "walltime": "00:01:00",
        "nodes": 1,
        "tasks_per_node": 2,
        "threads": 4,
    }

    js = JobScheduler.get_scheduler(props)
    actual = js.job_card.content()

    print(actual)
    print("***************")
    print(expected)
    assert actual == expected


def test_slurm4():
    expected = """#SBATCH --account=account_name
#SBATCH --qos=batch
#SBATCH --time=00:01:00
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=2
#SBATCH --mem=4MB"""

    props = {
        "scheduler": "slurm",
        "account": "account_name",
        "queue": "batch",
        "walltime": "00:01:00",
        "nodes": 1,
        "tasks_per_node": 2,
        "memory": "4MB",
    }

    js = JobScheduler.get_scheduler(props)
    actual = js.job_card.content()

    assert actual == expected


def test_slurm5():
    expected = """#SBATCH --account=account_name
#SBATCH --qos=batch
#SBATCH --time=00:01:00
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --exclusive=True"""

    props = {
        "scheduler": "slurm",
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


def test_lsf1():
    expected = """#BSUB -P account_name
#BSUB -q batch
#BSUB -W 00:01:00
#BSUB -R affinity[core(1)]
#BSUB -R span[ptile=1]
#BSUB -n 1"""

    props = {
        "scheduler": "lsf",
        "account": "account_name",
        "queue": "batch",
        "walltime": "00:01:00",
        "nodes": 1,
        "tasks_per_node": 1,
        "threads": 1,
    }

    js = JobScheduler.get_scheduler(props)
    actual = js.job_card.content()

    print(actual)
    print("***************")
    print(expected)
    assert actual == expected


def test_lsf2():
    expected = """#BSUB -P account_name
#BSUB -q batch
#BSUB -W 00:01:00
#BSUB -R affinity[core(1)]
#BSUB -R span[ptile=12]
#BSUB -n 12"""

    props = {
        "scheduler": "lsf",
        "account": "account_name",
        "queue": "batch",
        "walltime": "00:01:00",
        "nodes": 1,
        "tasks_per_node": 12,
        "threads": 1,
    }

    js = JobScheduler.get_scheduler(props)
    actual = js.job_card.content()

    assert actual == expected


def test_lsf3():
    expected = """#BSUB -P account_name
#BSUB -q batch
#BSUB -W 00:01:00
#BSUB -R affinity[core(1)]
#BSUB -R span[ptile=6]
#BSUB -n 12"""

    props = {
        "scheduler": "lsf",
        "account": "account_name",
        "queue": "batch",
        "walltime": "00:01:00",
        "nodes": 2,
        "tasks_per_node": 6,
        "threads": 1,
    }

    js = JobScheduler.get_scheduler(props)
    actual = js.job_card.content()

    print(actual)
    print("***************")
    print(expected)
    assert actual == expected
