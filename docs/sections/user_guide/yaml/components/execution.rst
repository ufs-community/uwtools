.. _execution_yaml:

The ``execution:`` Block
========================

Component drivers require an ``execution:`` block to provide details about how to configure a component's run-time environment, and how to run it.

Example block:

.. code-block:: yaml

   execution:
     batchargs:
       cores: 40
       debug: True
       exclusive: True
       export: NONE
       jobname: my-job
       memory: 4GB
       nodes: 1
       partition: p1
       queue: q1
       rundir: /path/to/rundir
       shell: /bin/bash
       stderr: /path/to/runscript.err
       stdout: /path/to/runscript.out
       tasks_per_node: 40
       walltime: 00:02:00
     envcmds:
       - module use /path/to/modulefiles
       - module load some_module
     executable: /path/to/sfc_climo_gen
     mpiargs:
       - "--export=ALL"
       - "--ntasks $SLURM_CPUS_ON_NODE"
     mpicmd: srun
     stacksize: 100M
     threads: 8

batchargs:
""""""""""

These entries map to job-scheduler directives sent to e.g. Slurm when a batch job is submitted via the ``--batch`` CLI switch or the ``batch=True`` API argument. The only **required** entry is ``walltime``.

Shorthand names are provided for certain directives for each scheduler, and can be specified as-so along with appropriate values. Recognized names for each scheduler are:

* LSF: ``jobname``, ``memory``, ``nodes``, ``queue``, ``shell``, ``stdout``, ``tasks_per_node``, ``walltime``
* PBS: ``debug``, ``jobname``, ``memory``, ``nodes``, ``queue``, ``shell``, ``stdout``, ``tasks_per_node``, ``walltime``
* Slurm: ``cores``, ``exclusive``, ``export``, ``jobname``, ``memory``, ``nodes``, ``partition``, ``queue``, ``rundir``, ``stderr``, ``stdout``, ``tasks_per_node``, ``walltime``

**NB** To enable threading when running components compiled with OpenMP support, set the ``execution:`` block's  ``threads:`` item (see below). Then ``uwtools`` will set the appropriate scheduler flag when making a batch request, and will set the ``OMP_NUM_THREADS`` environment variable in the execution environment.

Other, arbitrary directive key-value pairs can be provided exactly as they should appear in the batch runscript. For example

.. code-block:: yaml

   --nice: 100

could be specified to have the Slurm directive

.. code-block:: text

   #SBATCH --nice=100

included in the batch runscript.

envcmds:
""""""""

An **array** (YAML sequence) of commands to execute in the run-time shell before the component executable is run.

executable:
"""""""""""

The name of or path to the component's executable.

mpiargs:
""""""""

An **array** (YAML sequence) of string arguments that should follow the MPI launch program (``mpiexec``, ``srun``, et al.) on the command line. This entry is only used when configuring parallel components.

mpicmd:
"""""""

The MPI launch program (``mpiexec``, ``srun``, et al.). This entry is only used when configuring parallel components.

stacksize:
""""""""""

For drivers implementing support, exports the ``OMP_STACKSIZE`` environment variable to the execution environment, specifying the size of the stack for threads created by OpenMP. The value takes the form: *size* | *size*\ **B** | *size*\ **K** | *size*\ **M** | *size*\ **G**. When only *size* is provided, the unit is assumed to be kilobytes.

threads:
""""""""

For drivers implementing support, exports the ``OMP_NUM_THREADS`` environment variable to the execution environment, specifying the number of OpenMP threads to use when running the component. This entry is only used when configuring parallel components.
