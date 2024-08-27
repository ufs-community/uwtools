``orog``
========

.. include:: /shared/idempotent.rst

The ``uw`` mode for configuring and running the UFS Utils preprocessing component ``orog``.

.. literalinclude:: orog/help.cmd
   :language: text
   :emphasize-lines: 1
.. literalinclude:: orog/help.out
   :language: text

All tasks take the same arguments. For example:

.. literalinclude:: orog/run-help.cmd
   :language: text
   :emphasize-lines: 1
.. literalinclude:: orog/run-help.out
   :language: text

Examples
^^^^^^^^

The examples use a configuration file named ``config.yaml`` with contents similar to:

.. highlight:: yaml
.. literalinclude:: /shared/orog.yaml

Its contents are described in section :ref:`orog_yaml`.

* Run ``orog`` on an interactive node

  .. code-block:: text

     $ uw orog run --config-file config.yaml

  The driver creates a ``runscript.orog`` file in the directory specified by ``rundir:`` in the config and runs it, executing ``orog``.

* Run ``orog`` via a batch job

  .. code-block:: text

     $ uw orog run --config-file config.yaml --batch

  The driver creates a ``runscript.orog`` file in the directory specified by ``rundir:`` in the config and submits it to the batch system. Running with ``--batch`` requires a correctly configured ``platform:`` block in ``config.yaml``, as well as appropriate settings in the ``execution:`` block under ``orog:``.

* Specifying the ``--dry-run`` flag results in the driver logging messages about actions it would have taken, without actually taking any.

  .. code-block:: text

     $ uw orog run --config-file config.yaml --batch --dry-run

.. include:: /shared/key_path.rst

* Specifying the ``--show-schema`` flag, with no other options, prints the driver's schema:

.. literalinclude:: orog/show-schema.cmd
   :language: text
   :emphasize-lines: 1
.. literalinclude:: orog/show-schema.out
   :language: text
