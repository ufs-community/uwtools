from uwtools.scheduler import Scheduler

schedulers = ['Slurm', 'PBS']


def test_registered_schedulers():
    factory = Scheduler.scheduler_factory
    for sched in schedulers:
        assert factory.is_registered(sched), f"{sched} is not a registered Scheduler"
