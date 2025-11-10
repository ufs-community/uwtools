``mpassit``
===========

.. include:: ../shared/idempotent.rst

The ``uw`` mode for configuring and running the MPASSIT postprocessing tool. Each listed ``TASK`` may be called to generate the runtime asset(s) it is responsible for, and will call any task it depends on as needed. A ``provisioned_rundir`` comprises everything needed for a run, and a ``run`` runs the MPASSIT executable.

.. include:: help.rst

Examples
^^^^^^^^

The examples use a configuration file named ``config.yaml`` with contents similar to:

.. highlight:: yaml
.. literalinclude:: /shared/drivers/mpassit.yaml

Its contents are described in depth in section :ref:`mpassit_yaml`.

* Run MPASSIT on an interactive node

  .. code-block:: text

     $ uw mpassit run --config-file config.yaml --cycle 2025-02-12T12

  The driver creates a ``runscript.mpassit`` file in the directory specified by ``rundir:`` in the config and runs it, executing ``mpassit``.

* Run ``mpassit`` via a batch job

  .. code-block:: text

     $ uw mpassit run --config-file config.yaml --cycle 2025-02-12T12 --batch

  The driver creates a ``runscript.mpassit`` file in the directory specified by ``rundir:`` in the config and submits it to the batch system. Running with ``--batch`` requires a correctly configured ``platform:`` block in ``config.yaml``, as well as appropriate settings in the ``execution:`` block under ``mpassit:``.

* Specifying the ``--dry-run`` flag results in the driver logging messages about actions it would have taken, without actually taking any.

  .. code-block:: text

     $ uw mpassit run --config-file config.yaml --cycle 2025-02-12T12 --batch --dry-run

.. include:: /shared/key_path.rst

* The ``run`` task depends on the other available tasks and executes them as prerequisites. It is possible to execute any task directly, which entails execution of any of *its* dependencies. For example, to create an ``mpassit`` run directory provisioned with all the files, directories, symlinks, etc. required per the configuration file:

  .. code-block:: text

     $ uw mpassit provisioned_rundir --config-file config.yaml --cycle 2025-02-12T12 --batch

.. include:: schema-options.rst
