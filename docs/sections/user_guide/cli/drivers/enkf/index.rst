``enkf``
========

.. include:: ../shared/idempotent.rst

The ``uw`` mode for configuring and running the EnKF data assimilation tool. Each listed ``TASK`` may be called to generate the runtime asset(s) it is responsible for, and will call any task it depends on as needed. A ``provisioned_rundir`` comprises everything needed for a run, and a ``run`` runs the EnKF executable.

.. include:: help.rst

Examples
^^^^^^^^

The examples use a configuration file named ``config.yaml`` with contents similar to:

.. highlight:: yaml
.. literalinclude:: /shared/enkf.yaml

Its contents are described in depth in section :ref:`enkf_yaml`.

* Run EnKF on an interactive node

  .. code-block:: text

     $ uw enkf run --config-file config.yaml --cycle 2025-02-12T12

  The driver creates a ``runscript.enkf`` file in the directory specified by ``rundir:`` in the config and runs it, executing ``enkf``.

* Run ``enkf`` via a batch job

  .. code-block:: text

     $ uw enkf run --config-file config.yaml --cycle 2025-02-12T12 --batch

  The driver creates a ``runscript.enkf`` file in the directory specified by ``rundir:`` in the config and submits it to the batch system. Running with ``--batch`` requires a correctly configured ``platform:`` block in ``config.yaml``, as well as appropriate settings in the ``execution:`` block under ``enkf:``.

* Specifying the ``--dry-run`` flag results in the driver logging messages about actions it would have taken, without actually taking any.

  .. code-block:: text

     $ uw enkf run --config-file config.yaml --cycle 2025-02-12T12 --batch --dry-run

.. include:: /shared/key_path.rst

* The ``run`` task depends on the other available tasks and executes them as prerequisites. It is possible to execute any task directly, which entails execution of any of *its* dependencies. For example, to create an ``enkf`` run directory provisioned with all the files, directories, symlinks, etc. required per the configuration file:

  .. code-block:: text

     $ uw enkf provisioned_rundir --config-file config.yaml --cycle 2025-02-12T12 --batch

.. include:: schema-options.rst
