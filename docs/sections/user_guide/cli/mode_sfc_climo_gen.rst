Mode ``sfc_climo_gen``
======================

The ``uw`` mode for configuring and running the :sfc-climo-gen:`sfc_climo_gen<>` component.

.. code-block:: text

   $ uw sfc_climo_gen --help
   usage: uw sfc_climo_gen [-h] TASK ...

   Execute sfc_climo_gen tasks

   Optional arguments:
     -h, --help
         Show help and exit

   Positional arguments:
     TASK
       namelist_file
         The namelist file
       provisioned_run_directory
         Run directory provisioned with all required content
       run
         Run execution
       runscript
         The runscript

All tasks take the same arguments. For example:

.. code-block:: text

   $ uw sfc_climo_gen run --help
   usage: uw sfc_climo_gen run --config-file PATH [-h] [--batch] [--dry-run] [--debug] [--quiet]
                               [--verbose]

   Run execution

   Required arguments:
     --config-file PATH, -c PATH
         Path to config file

   Optional arguments:
     -h, --help
         Show help and exit
     --batch
         Submit run to batch scheduler
     --dry-run
         Only log info, making no changes
     --debug
         Print all log messages, plus any unhandled exception's stack trace (implies --verbose)
     --quiet, -q
         Print no logging messages
     --verbose, -v
         Print all logging messages


Examples
^^^^^^^^

The examples use a configuration file named ``config.yaml`` with content similar to:

.. highlight:: yaml
.. literalinclude:: ../../../shared/sfc_climo_gen.yaml

Its contents are described in depth in section :ref:`sfc_climo_gen_yaml`.

* Run ``sfc_climo_gen`` on an interactive node

  .. code-block:: text

     $ uw sfc_climo_gen run --config-file config.yaml

  The driver creates a ``runscript`` file in the directory specified by ``run_dir:`` in the config and runs it, executing ``sfc_climo_gen``.

* Run ``sfc_climo_gen`` via a batch job

  .. code-block:: text

     $ uw sfc_climo_gen run --config-file config.yaml --batch

  The driver creates a ``runscript`` file in the directory specified by ``run_dir:`` in the config and submits it to the batch system. Running with ``--batch`` requires a correctly configured ``platform:`` block in ``config,yaml``, as well as appropriate settings in the ``execution:`` block under ``sfc_climo_gen:``.

* Specifying the ``--dry-run`` flag results in the driver logging messages about actions it would have taken, without actually taking any.

  .. code-block:: text

     $ uw sfc_climo_gen run --config-file config.yaml --batch --dry-run

* The ``run`` task depends on the other available tasks and executes them as prerequisites. It is possible to execute any task directly, which entails execution of any of *its* dependencies. For example, to create an ``sfc_climo_gen`` run directory provisioned with all the files, directories, symlinks, etc. required per the configuration file:

  .. code-block:: text

     $ uw sfc_climo_gen provisioned_run_directory --config-file config.yaml --batch
