import collections


from uwtools.scheduler import slurm


class JobCard(collections.UserList):
    def content(self, line_separator="\n"):
        return line_separator.join(self)


MAP_SCHEDULER = {"slurm": slurm.Slurm, "pbs": slurm.PBS, "lsf": slurm.LSF, object: None}


class JobScheduler(collections.UserDict):

    _map = {}
    prefix = ""

    def __getattr__(self, name):
        if name in self:
            return self[name]

    @property
    def job_card(self) -> JobCard:
        return JobCard(
            [f"{self.prefix}{self._map[key]}{value}" for (key, value) in self.items()]
        )

    @classmethod
    def get_scheduler(cls, props):
        return MAP_SCHEDULER[props.scheduler](props)
