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
#PBS select #PBS -l select=4:mpiprocs=4:ompthreads=4:ncpus=16"""

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
