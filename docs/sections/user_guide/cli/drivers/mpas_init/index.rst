``mpas_init``
=============

.. include:: ../shared/idempotent.rst

The ``uw`` mode for configuring and running the MPAS ``init_atmosphere`` tool. Each listed ``TASK`` may be called to generate the runtime asset(s) it is responsible for, and will call any task it depends on as needed. A ``provisioned_rundir`` comprises everything needed for a run, and a ``run`` runs the ``init_atmosphere`` executable.

.. include:: help.rst

Examples
^^^^^^^^

The examples use a configuration file named ``config.yaml`` with contents similar to:

.. highlight:: yaml
.. literalinclude:: /shared/mpas_init.yaml

Its contents are described in depth in section :ref:`mpas_init_yaml`.

* Run ``init_atmosphere`` on an interactive node

  .. code-block:: text

     $ uw mpas_init run --config-file config.yaml --cycle 2023-12-18T00

  The driver creates a ``runscript.mpas_init`` file in the directory specified by ``rundir:`` in the config and runs it, executing ``init_atmosphere``.

* Run ``init_atmosphere`` via a batch job

  .. code-block:: text

     $ uw mpas_init run --config-file config.yaml --cycle 2023-12-18T00 --batch

  The driver creates a ``runscript.mpas_init`` file in the directory specified by ``rundir:`` in the config and submits it to the batch system. Running with ``--batch`` requires a correctly configured ``platform:`` block in ``config.yaml``, as well as appropriate settings in the ``execution:`` block under ``mpas_init:``.

* Specifying the ``--dry-run`` flag results in the driver logging messages about actions it would have taken, without actually taking any.

  .. code-block:: text

     $ uw mpas_init run --config-file config.yaml --cycle 2023-12-18T00 --batch --dry-run

.. include:: /shared/key_path.rst

* The ``run`` task depends on the other available tasks and executes them as prerequisites. It is possible to execute any task directly, which entails execution of any of *its* dependencies. For example, to create an ``mpas_init`` run directory provisioned with all the files, directories, symlinks, etc. required per the configuration file:

  .. code-block:: text

     $ uw mpas_init provisioned_rundir --config-file config.yaml --cycle 2023-12-18T00 --batch

.. include:: schema-options.rst
