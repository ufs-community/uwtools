``ungrib``
==========

.. include:: ../shared/idempotent.rst

The ``uw`` mode for configuring and running the WRF preprocessing component ``ungrib``. Documentation for this component is :wps:`here <>`.

.. include:: help.rst

Examples
^^^^^^^^

The examples use a configuration file named ``config.yaml`` with contents similar to:

.. highlight:: yaml
.. literalinclude:: /shared/ungrib.yaml

Its contents are described in depth in section :ref:`ungrib_yaml`.

* Run ``ungrib`` on an interactive node

  .. code-block:: text

     $ uw ungrib run --config-file config.yaml --cycle 2021-04-01T12

  The driver creates a ``runscript.ungrib`` file in the directory specified by ``rundir:`` in the config and runs it, executing ``ungrib``.

* Run ``ungrib`` via a batch job

  .. code-block:: text

     $ uw ungrib run --config-file config.yaml --cycle 2021-04-01T12 --batch

  The driver creates a ``runscript.ungrib`` file in the directory specified by ``rundir:`` in the config and submits it to the batch system. Running with ``--batch`` requires a correctly configured ``platform:`` block in ``config.yaml``, as well as appropriate settings in the ``execution:`` block under ``ungrib:``.

* Specifying the ``--dry-run`` flag results in the driver logging messages about actions it would have taken, without actually taking any.

  .. code-block:: text

     $ uw ungrib run --config-file config.yaml --cycle 2021-04-01T12 --batch --dry-run

.. include:: /shared/key_path.rst

* The ``run`` task depends on the other available tasks and executes them as prerequisites. It is possible to execute any task directly, which entails execution of any of *its* dependencies. For example, to create an ``ungrib`` run directory provisioned with all the files, directories, symlinks, etc. required per the configuration file:

  .. code-block:: text

     $ uw ungrib provisioned_rundir --config-file config.yaml --cycle 2021-04-01T12 --batch

.. include:: schema-options.rst
