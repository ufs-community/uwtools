# pylint: disable=all
import pytest

from uwtools.scheduler import JobScheduler


def test_dummy():
    """Skip the test. Used only as a placeholder."""
    return True


def test_scheduler():

    expected = """#SBATCH scheduler=slurm
#SBATCH --job-name=abcd
#SBATCH extra_stuff=12345"""

    props = {"scheduler": "slurm", "job_name": "abcd", "extra_stuff": "12345"}

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
