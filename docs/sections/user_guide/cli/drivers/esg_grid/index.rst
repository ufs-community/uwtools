``esg_grid``
============

.. include:: ../shared/idempotent.rst

The ``uw`` mode for configuring and running the UFS Utils preprocessing component ``regional_esg_grid``. Documentation for this UFS Utils component is :ufs-utils:`here <regional-esg-grid>`.

.. include:: help.rst

Examples
^^^^^^^^

The examples use a configuration file named ``config.yaml`` with contents similar to:

.. highlight:: yaml
.. literalinclude:: /shared/esg_grid.yaml

Its contents are described in depth in section :ref:`esg_grid_yaml`.

* Run ``esg_grid`` on an interactive node

  .. code-block:: text

     $ uw esg_grid run --config-file config.yaml

  The driver creates a ``runscript.esg_grid`` file in the directory specified by ``rundir:`` in the config and runs it, executing ``esg_grid``.

* Run ``esg_grid`` via a batch job

  .. code-block:: text

     $ uw esg_grid run --config-file config.yaml --batch

The driver creates a ``runscript.esg_grid`` file in the directory specified by ``rundir:`` in the config and submits it to the batch system. Running with ``--batch`` requires a correctly configured ``platform:`` block in ``config.yaml``, as well as appropriate settings in the ``execution:`` block under ``esg_grid:``.

* Specifying the ``--dry-run`` flag results in the driver logging messages about actions it would have taken, without actually taking any.

  .. code-block:: text

     $ uw esg_grid run --config-file config.yaml --batch --dry-run

.. include:: /shared/key_path.rst

* The ``run`` task depends on the other available tasks and executes them as prerequisites. It is possible to execute any task directly, which entails execution of any of *its* dependencies. For example, to create an ``esg_grid`` run directory provisioned with all the files, directories, symlinks, etc. required per the configuration file:

  .. code-block:: text

     $ uw esg_grid provisioned_rundir --config-file config.yaml --batch

.. include:: schema-options.rst
