#!/usr/bin/env python3

from uwtools.scheduler import Scheduler

config = {'account': 'da-cpu',
          'queue': 'batch'}

sfac = Scheduler.scheduler_factory
print(type(sfac))
print(sfac.registered())
pbs = sfac.create('PBS', config)
pbs.echo()
slurm = sfac.create('Slurm', config)
slurm.echo()
print(slurm._config['account'])
print(slurm._config['queue'])
pbs2 = sfac.create('PBS', config)
whos()
sfac.destroy('PBS')
sfac.destroy('me')
print(sfac.registered())

