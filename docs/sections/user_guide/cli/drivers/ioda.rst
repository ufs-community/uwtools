``ioda``
========

.. include:: /shared/idempotent.rst

The ``uw`` mode for configuring and running the IODA components of the JEDI framework.

.. literalinclude:: ioda/help.cmd
   :language: text
   :emphasize-lines: 1
.. literalinclude:: ioda/help.out
   :language: text

All tasks take the same arguments. For example:

.. literalinclude:: ioda/run-help.cmd
   :language: text
   :emphasize-lines: 1
.. literalinclude:: ioda/run-help.out
   :language: text

Examples
^^^^^^^^

The examples use a configuration file named ``config.yaml`` with contents similar to:

.. highlight:: yaml
.. literalinclude:: /shared/ioda.yaml

Its contents are described in section :ref:`ioda_yaml`.

* Run ``ioda`` on an interactive node

   .. code-block:: text

      $ uw ioda run --config-file config.yaml --cycle 2024-05-22T12

The driver creates a ``runscript.ioda`` file in the directory specified by ``rundir:`` in the config and runs it, executing ``ioda``.

* Run ``ioda`` via a batch job

   .. code-block:: text

      $ uw ioda run --config-file config.yaml --cycle 2024-05-22T12 --batch

The driver creates a ``runscript.ioda`` file in the directory specified by ``rundir:`` in the config and submits it to the batch system. Running with ``--batch`` requires a correctly configured ``platform:`` block in ``config.yaml``, as well as appropriate settings in the ``execution:`` block under ``ioda:``.

* Specifying the ``--dry-run`` flag results in the driver logging messages about actions it would have taken, without actually taking any.

  .. code-block:: text

     $ uw ioda run --config-file config.yaml --cycle 2024-05-22T12 --batch --dry-run

.. include:: /shared/key_path.rst

* Specifying the ``--show-schema`` flag, with no other options, prints the driver's schema:

.. literalinclude:: ioda/show-schema.cmd
   :language: text
   :emphasize-lines: 1
.. literalinclude:: ioda/show-schema.out
   :language: text
