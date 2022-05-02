# pylint: disable=all
import pytest

from uwtools.scheduler import JobScheduler


def test_scheduler_slurm():

    expected = """#SBATCH --job-name=abcd
#SBATCH extra_stuff=12345"""

    props = {"scheduler": "slurm", "job_name": "abcd", "extra_stuff": "12345"}

    js = JobScheduler.get_scheduler(props)
    actual = js.job_card.content()

    assert actual == expected


def test_scheduler_lsf():

    expected = """#BSUB -J abcd
#BSUB -n 48
#BSUB extra_stuff 12345"""

    props = {
        "scheduler": "lsf",
        "job_name": "abcd",
        "extra_stuff": "12345",
        "nodes": "12",
        "tasks_per_node": "4",
    }

    js = JobScheduler.get_scheduler(props)
    actual = js.job_card.content()

    assert actual == expected


def test_scheduler_pbs():

    expected = """#PBS cpus 2
#PBS -l select=4:mpiprocs=4:ompthreads=4:ncpus=16:mem=8gb"""

    props = {
        "scheduler": "pbs",
        "nodes": "4",
        "threads": "12345",
        "cpus": "2",
        "threads": "4",
        "tasks_per_node": "4",
        "memory": "8gb",
    }

    js = JobScheduler.get_scheduler(props)
    actual = js.job_card.content()

    print(actual)
    print("--------------")
    print(expected)
    assert actual == expected


def test_scheduler_dot_notation():

    props = {"scheduler": "slurm", "job_name": "abcd", "extra_stuff": "12345"}

    js = JobScheduler.get_scheduler(props)
    expected = "abcd"
    actual = js.job_name

    assert actual == expected


def test_scheduler_prop_not_defined_raises_key_error():
    with pytest.raises(KeyError) as error:
        props = {
            "job_name": "abcd",
            "extra_stuff": "12345",
        }

        JobScheduler.get_scheduler(props)
    expected = "no scheduler defined in props: [job_name, extra_stuff]"
    actual = str(error.value)
    assert expected in actual


def test_scheduler_known_args():

    expected = """#SBATCH --nodes=12
#SBATCH --job-name=abcd
#SBATCH --extra_arg=12345
#SBATCH --extra-flags"""

    props = {
        "nodes": "12",
        "scheduler": "slurm",
        "job_name": "abcd",
        "--extra_arg": "12345",
        "--extra-flags": "",
    }

    js = JobScheduler.get_scheduler(props)
    actual = js.job_card.content()

    assert actual == expected


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

    print(actual)
    print("*" * 8)
    print(expected)
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

    assert actual == expected
