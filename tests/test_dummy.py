

# pylint: disable=unused-variable
from src.uwtools.scheduler import JobScheduler


def test_dummy():
    ''' Skip the test. Used only as a placeholder. '''
    return True

def test_scheduler():
    
    
    expected = """#SBATCH scheduler=slurm
#SBATCH --job-name=abcd
#SBATCH extra_stuff=12345"""

    props = {
            "scheduler": "slurm",
            "job_name": "abcd",
            "extra_stuff": "12345"
        }

    js = JobScheduler.get_scheduler(props)
    actual = js.job_card.content()
    
    assert actual == expected
    
