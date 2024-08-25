``upp``
=======

.. include:: ../shared/idempotent.rst

The ``uw`` mode for configuring and running the `UPP <https://epic.noaa.gov/unified-post-processor/>`_ component.

.. include:: help.rst

Examples
^^^^^^^^

The examples use a configuration file named ``config.yaml`` with contents similar to:

.. highlight:: yaml
.. literalinclude:: /shared/upp.yaml

Its contents are described in depth in section :ref:`upp_yaml`.

* Run ``upp`` on an interactive node

  .. code-block:: text

     $ uw upp run --config-file config.yaml --cycle 2024-05-06T12 --leadtime 6

  The driver creates a ``runscript.upp`` file in the directory specified by ``rundir:`` in the config and runs it, executing ``upp``.

* Run ``upp`` via a batch job

  .. code-block:: text

     $ uw upp run --config-file config.yaml --cycle 2024-05-06T12 --leadtime 6 --batch

  The driver creates a ``runscript.upp`` file in the directory specified by ``rundir:`` in the config and submits it to the batch system. Running with ``--batch`` requires a correctly configured ``platform:`` block in ``config.yaml``, as well as appropriate settings in the ``execution:`` block under ``upp:``.

* Specifying the ``--dry-run`` flag results in the driver logging messages about actions it would have taken, without actually taking any.

  .. code-block:: text

     $ uw upp run --config-file config.yaml --cycle 2024-05-06T12 --leadtime 6 --batch --dry-run

.. include:: /shared/key_path.rst

* The ``run`` task depends on the other available tasks and executes them as prerequisites. It is possible to execute any task directly, which entails execution of any of *its* dependencies. For example, to create an ``upp`` run directory provisioned with all the files, directories, symlinks, etc. required per the configuration file:

  .. code-block:: text

     $ uw upp provisioned_rundir --config-file config.yaml --cycle 2024-05-06T12 --leadtime 6 --batch

* Specifying the ``--show-schema`` flag, with no other options, prints the driver's schema:

.. literalinclude:: show-schema.cmd
   :language: text
   :emphasize-lines: 1
.. literalinclude:: show-schema.out
   :language: text
