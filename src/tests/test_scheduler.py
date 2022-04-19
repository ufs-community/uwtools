#!/usr/bin/env python3

from uwtools.scheduler import Scheduler

schedulers = ['Slurm', 'PBS']
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

def compare_jobcards(reference, test):
    try:
        with open(test, 'r') as fh:
            test_out = fh.readlines()
    except Exception as e:
        raise AssertionError(f"failed reading {test} as {e}")

    reference_out = reference.splitlines()
    for ref, tst in zip(reference_out, test_out):
        assert ref.strip() == tst.strip(), f"Incorrect match {ref} /= {tst}"

def test_registered_schedulers():
    factory = Scheduler.scheduler_factory
    for sched in schedulers:
        assert factory.is_registered(sched), f"{sched} is not a registered Scheduler"

def test_slurm1():
    factory = Scheduler.scheduler_factory
    sched = factory.create('Slurm', slurm1)
    sched.dump(filename='slurm1.out')
    compare_jobcards(slurm1_ref, 'slurm1.out')

def test_slurm2():
    factory = Scheduler.scheduler_factory
    sched = factory.create('Slurm', slurm2)
    sched.dump(filename='slurm2.out')
    compare_jobcards(slurm2_ref, 'slurm2.out')


test_registered_schedulers()
test_slurm1()
test_slurm2()
#test_registered_schedulers()
#def test_slurm:
#    factory = Scheduler.scheduler_factory

#sfac = Scheduler.scheduler_factory
#print(type(sfac))
#print(sfac.registered)
#pbs = sfac.create('PBS', config)
#pbs.echo()
#slurm = sfac.create('Slurm', config)
#slurm.echo()
#print(slurm._config['account'])
#print(slurm._config['queue'])
#pbs2 = sfac.create('PBS', config)
#whos()
#sfac.destroy('PBS')
#sfac.destroy('me')
#print(sfac.registered)

