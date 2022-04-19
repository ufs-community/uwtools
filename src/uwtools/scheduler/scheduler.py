from datetime import timedelta
from ..factory import Factory
from ..nameddict import NamedDict


class Scheduler:

    scheduler_factory = Factory('Scheduler')

    _DIRECTIVE = None

    def __init__(self, config: dict, *args, **kwargs):
        """

        Parameters
        ----------
        config : dict
        """
        # Cache incoming config
        self._config = NamedDict(config)
        self.specs = self._config_to_specs
        self.batch_card = []

        pass

    def echo(self):
        print(f'Base directive is {self._DIRECTIVE}')

    @property
    def _config_to_specs(self):
        specs = self._config

        # Convert 'memory' to MB
        if 'memory' in self._config:
            specs.memory = str(self.memory_in_megabytes(self._config.memory)) + 'M'

        # Convert 'walltime' to HH:MM:SS format
        if 'walltime' in self._config:
            specs.walltime = self.walltime_in_string(self._config.walltime)

        # Ensure environment variables are a list
        if 'env' in self._config:
            if not isinstance(self._config.env, (list, tuple)):
                specs.env = [self._config.env]

        # Ensure native scheduler directives are a list
        if 'native' in self._config:
            if not isinstance(self._config.native, (list, tuple)):
                specs.native = [self._config.native]

        return specs

    def dump(self, filename=None):
        """
        Method to dump out the batch card either to file or stdout
        Parameters
        ----------
        filename

        Returns
        -------
        None
        """
        if filename is not None:
            try:
                with open(filename, 'w') as fh:
                    for item in self.batch_card:
                        fh.write(f"{item}\n")
            except Exception as e:
                raise f"Unknown exception in writing scheduler directives to {filename} as {e}"
        else:
            print(self.get_batch_card)

    @property
    def get_batch_card(self):
        return '\n'.join(self.batch_card)


    @classmethod
    def memory_in_bytes(cls, memory: str):
        """
        Converts bytes, k, M, G, T (case-insensitive) to number of bytes
        Default units of input memory string is bytes
        Uses powers of 1024 for scaling (kilobytes, megabytes, etc.)
        1024 Bytes = 1 KB

        Parameters
        ----------
        memory

        Returns
        -------
        int: memory in bytes
        """
        scale = {'B': 0, 'K': 1, 'M': 2, 'G': 3, 'T': 4}
        multiplier = 1
        if memory[-1].upper() in scale:
            multiplier = 1024 ** scale[memory[-1]]
            memory = memory[:-1]
        return float(memory) * multiplier

    @classmethod
    def memory_in_megabytes(cls, memory: str):
        """
        Converts input memory in bytes into Megabytes
        1 MB = 1048576 Bytes
        """
        return int(Scheduler.memory_in_bytes(memory) / 1048576.0)

    @classmethod
    def walltime_in_string(cls, walltime):
        if isinstance(walltime, timedelta):
            total_seconds = walltime.total_seconds()
            hours = (total_seconds // 3600) % 24
            minutes = (total_seconds // 60) % 60
            seconds = total_seconds % 60
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        else:  # walltime is not a timedelta, likely is already in the 'HH:MM:SS' format
            return walltime
