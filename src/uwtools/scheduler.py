import collections
class JobCard(collections.UserList):
    
    def content(self, line_separator="\n"):
        return line_separator.join(self)

class JobScheduler(collections.UserDict):
    
    _map = {}
    prefix = ""

    def __getattr__(self, name):
        if name in self:
            return self[name]

    @property
    def job_card(self):
        return JobCard([f"{self.prefix} {self._map[key] if key in self._map else key + '='}{value}" for (key, value) in self.items()])

        

    @classmethod
    def get_scheduler(cls, props):
        print(props)
        MAP_SCHEDULER = {"slurm": Slurm, "pbs": PBS, "lsf": LSF, object: None}
        return MAP_SCHEDULER[props['scheduler']](props)

class Slurm(JobScheduler):
    prefix = "#SBATCH"

    _map = {
        "job_name": "--job-name=",
        "output": "--output=",
        "error": "--error=",
        "wall_time": "--time=",
        "partition": "--partition=",
        "account": "--account=",
        "nodes": "--nodes=",
        "number_tasks": "--ntasks-per-node=",
    }


class Bash(JobScheduler):
    prefix = ""


class PBS(JobScheduler):
    prefix = "#PBS"

    _map = {
        "bash": "-S",
        "job_name": "-N",
        "output": "-o",
        "job_name": "-j",
        "queue": "-q",
        "account": "-A",
        "wall_time": "-l walltime=",
        "total_nodes": "-l select=",
        "cpus": "cpus=",
        "place": "-l place=",
        "debug": "-l debug=",
    }


class LSF(JobScheduler):
    _map = {
        "bash": "-L",
        "job_name": "-J",
        "output": "-o",
        "queue": "-q",
        "account": "-P",
        "wall_time": "-W",
        "total_nodes": "-n",
        "cpus": "-R affinity[core()]",  # TODO
        "number_tasks": "-R span[ptile=]",  # TODO
        "change_dir": "-cwd /tmp",
    }

    prefix = "#BSUB"

if __name__ == "__main__":
    props = {
        "scheduler": "slurm",
        "job_name": "abcd",
        "extra_stuff": "12345"
    }

    js = JobScheduler.get_scheduler(props)
    with open("xyz.txt", "w") as _file:
        _file.write(js.job_card.content())
    
    