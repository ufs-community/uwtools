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
          'shell': '/bin/bash'
          }

pbs1 = config
pbs1_ref = """#PBS -S /bin/bash
#PBS -N JOB_NAME
#PBS -A ACCOUNT_NAME
#PBS -q QUEUE_NAME
#PBS -o job.out
#PBS -l walltime=01:00:00
#PBS -l debug=True
#PBS -l select=1:mpiprocs=5
"""

pbs2 = config.copy()
pbs2_upd = {'debug': True,
            'exclusive': True,
            'join': True,
            'memory': '512M',
            'nodes': 2,
            'tasks': 24,
            'threads': 2,
            'env': ['ARG1'],
            'native': '-R MySlot'}
pbs2.update(pbs2_upd)
pbs2_ref = """#PBS -S /bin/bash
#PBS -N JOB_NAME
#PBS -A ACCOUNT_NAME
#PBS -q QUEUE_NAME
#PBS -j oe
#PBS -o job.out
#PBS -l walltime=01:00:00
#PBS -l debug=True
#PBS -l select=2:mpiprocs=5:ompthreads=2:ncpus=24:mem=512M
#PBS -l place=excl
#PBS -R MySlot
#PBS -v ARG1=None"""


def test_pbs1(tmp_path, read_file):
    """
    Test for pbs1 configuration
    Parameters
    ----------
    tmp_path - pytest fixture
    read_file - custom pytest fixture in conftest.py

    Returns
    -------

    """
    factory = Scheduler.scheduler_factory
    sched = factory.create('PBS', pbs1)
    testfile = tmp_path / 'pbs1.out'
    sched.dump(filename=testfile)
    test_card = read_file(testfile)
    for ref, tst in zip(pbs1_ref.splitlines(), test_card):
        assert ref.strip() == tst.strip(), f"Incorrect match {ref} /= {tst}"


def test_pbs2(tmp_path, read_file):
    factory = Scheduler.scheduler_factory
    sched = factory.create('PBS', pbs2)
    testfile = tmp_path / 'pbs2.out'
    sched.dump(filename=testfile)
    test_card = read_file(testfile)
    for ref, tst in zip(pbs2_ref.splitlines(), test_card):
        assert ref.strip() == tst.strip(), f"Incorrect match {ref} /= {tst}"
