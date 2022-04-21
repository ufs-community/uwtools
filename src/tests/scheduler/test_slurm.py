from uwtools.scheduler import Scheduler


config = {'account': 'ACCOUNT_NAME',
          'queue': 'QUEUE_NAME',
          'jobname': 'JOB_NAME',
          'join': False,
          'stdout': 'job.out',
          'stderr': 'job.err',
          'walltime': '01:00:00',
          'nodes': 1,
          'tasks_per_node': 5,
          'debug': True,
          'exclusive': False,
          }

slurm1 = config
slurm1_ref = """#SBATCH --job-name=JOB_NAME
#SBATCH --account=ACCOUNT_NAME
#SBATCH --qos=QUEUE_NAME
#SBATCH --output=job.out
#SBATCH --error=job.err
#SBATCH --time=01:00:00
#SBATCH --nodes=1
#SBATCH --ntasks_per-node=5
#SBATCH --verbose
"""

slurm2 = config.copy()
slurm2_upd = {'debug': True,
              'exclusive': True,
              'memory': '512M',
              'env': ['HOME', 'ARG1=test'],
              'native': '--reservation=MySlot'}
slurm2.update(slurm2_upd)
slurm2_ref = """#SBATCH --job-name=JOB_NAME
#SBATCH --account=ACCOUNT_NAME
#SBATCH --qos=QUEUE_NAME
#SBATCH --output=job.out
#SBATCH --error=job.err
#SBATCH --mem=512M
#SBATCH --time=01:00:00
#SBATCH --nodes=1
#SBATCH --ntasks_per-node=5
#SBATCH --exclusive
#SBATCH --verbose
#SBATCH --reservation=MySlot
#SBATCH --export=HOME
#SBATCH --export=ARG1=test"""


def test_slurm1(tmp_path, read_file):
    """
    Test for slurm1 configuration
    Parameters
    ----------
    tmp_path - pytest fixture
    read_file - custom pytest fixture in conftest.py

    Returns
    -------

    """
    factory = Scheduler.scheduler_factory
    sched = factory.create('Slurm', slurm1)
    testfile = tmp_path / 'slurm1.out'
    sched.dump(filename=testfile)
    test_card = read_file(testfile)
    for ref, tst in zip(slurm1_ref.splitlines(), test_card):
        assert ref.strip() == tst.strip(), f"Incorrect match {ref} /= {tst}"


def test_slurm2(tmp_path, read_file):
    factory = Scheduler.scheduler_factory
    sched = factory.create('Slurm', slurm2)
    testfile = tmp_path / 'slurm2.out'
    sched.dump(filename=testfile)
    test_card = read_file(testfile)
    for ref, tst in zip(slurm2_ref.splitlines(), test_card):
        assert ref.strip() == tst.strip(), f"Incorrect match {ref} /= {tst}"
