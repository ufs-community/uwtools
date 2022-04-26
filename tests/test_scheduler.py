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


def test_scheduler_lfs():

    expected = """#BSUB -J abcd
#BSUB extra_stuff 12345"""

    props = {"scheduler": "lsf", "job_name": "abcd", "extra_stuff": "12345"}

    js = JobScheduler.get_scheduler(props)
    actual = js.job_card.content()

    assert actual == expected


def test_scheduler_pbs():

    expected = """#PBS -N abcd
#PBS extra_stuff 12345"""

    props = {"scheduler": "pbs", "job_name": "abcd", "extra_stuff": "12345"}

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

    expected = """#SBATCH --extra-flags
#SBATCH --extra_arg=12345
#SBATCH --job-name=abcd"""

    props = {
        "scheduler": "slurm",
        "job_name": "abcd",
        "--extra_arg": "12345",
        "--extra-flags": "",
    }

    js = JobScheduler.get_scheduler(props)
    actual = js.job_card.content()

    assert actual == expected
