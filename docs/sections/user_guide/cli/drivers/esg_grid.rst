``esg_grid``
============

The ``uw`` mode for configuring and running the :ufs-utils:`esg_grid<regional-esg-grid>` component.

.. code-block:: text

   $ uw esg_grid --help
    usage: uw esg_grid [-h] [--version] TASK ...
    
    Execute Esg Grid tasks
    
    Optional arguments:
      -h, --help
          Show help and exit
      --version
          Show version info and exit
    
    Positional arguments:
      TASK
        namelist_file
          The namelist file
        provisioned_run_directory
          Run directory provisioned with all required content
        run
          A run
        runscript
          The runscript
        validate
          Validate the UW driver config

All tasks take the same arguments. For example:

.. code-block:: text

    $ uw esg_grid run --help
    usage: uw esg_grid run --config-file PATH [-h] [--version] [--batch] [--dry-run] [--graph-file PATH] [--quiet] [--verbose]
    
    A run
    
    Required arguments:
      --config-file PATH, -c PATH
          Path to config file
    
    Optional arguments:
      -h, --help
          Show help and exit
      --version
          Show version info and exit
      --batch
          Submit run to batch scheduler
      --dry-run
          Only log info, making no changes
      --graph-file PATH
          Path to Graphviz DOT output [experimental]
      --quiet, -q
          Print no logging messages
      --verbose, -v
          Print all logging messages

Examples
^^^^^^^^

The examples use a configuration file named ``config.yaml`` with content similar to:

.. highlight:: yaml
.. literalinclude:: ../../../../shared/esg_grid.yaml

Its contents are described in depth in section :ref:`esg_grid_yaml`.

* Run ``esg_grid`` on an interactive node

  .. code-block:: text

     $ uw esg_grid run --config-file config.yaml

  The driver creates a ``runscript.esg_grid`` file in the directory specified by ``run_dir:`` in the config and runs it, executing ``esg_grid``.

* Run ``esg_grid`` via a batch job

  .. code-block:: text

     $ uw esg_grid run --config-file config.yaml --batch

The driver creates a ``runscript.esg_grid`` file in the directory specified by ``run_dir:`` in the config and submits it to the batch system. Running with ``--batch`` requires a correctly configured ``platform:`` block in ``config.yaml``, as well as appropriate settings in the ``execution:`` block under ``esg_grid:``.

* Specifying the ``--dry-run`` flag results in the driver logging messages about actions it would have taken, without actually taking any.

  .. code-block:: text

     $ uw esg_grid run --config-file config.yaml --batch --dry-run

* The ``run`` task depends on the other available tasks and executes them as prerequisites. It is possible to execute any task directly, which entails execution of any of *its* dependencies. For example, to create an ``esg_grid`` run directory provisioned with all the files, directories, symlinks, etc. required per the configuration file:

  .. code-block:: text

     $ uw esg_grid provisioned_run_directory --config-file config.yaml --batch
