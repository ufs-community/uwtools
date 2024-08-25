``jedi``
========

.. include:: /shared/idempotent.rst

The ``uw`` mode for configuring and running the JEDI framework.

.. literalinclude:: jedi/help.cmd
   :language: text
   :emphasize-lines: 1
.. literalinclude:: jedi/help.out
   :language: text

All tasks take the same arguments. For example:

.. literalinclude:: jedi/run-help.cmd
   :language: text
   :emphasize-lines: 1
.. literalinclude:: jedi/run-help.out
   :language: text

Examples
^^^^^^^^

The examples use a configuration file named ``config.yaml`` with contents similar to:

.. highlight:: yaml
.. literalinclude:: /shared/jedi.yaml

Its contents are described in section :ref:`jedi_yaml`.

* Run ``jedi`` on an interactive node

   .. code-block:: text

      $ uw jedi run --config-file config.yaml --cycle 2024-05-22T12

The driver creates a ``runscript.jedi`` file in the directory specified by ``rundir:`` in the config and runs it, executing ``jedi``.

* Run ``jedi`` via a batch job

   .. code-block:: text

      $ uw jedi run --config-file config.yaml --cycle 2024-05-22T12 --batch

The driver creates a ``runscript.jedi`` file in the directory specified by ``rundir:`` in the config and submits it to the batch system. Running with ``--batch`` requires a correctly configured ``platform:`` block in ``config.yaml``, as well as appropriate settings in the ``execution:`` block under ``jedi:``.

* Specifying the ``--dry-run`` flag results in the driver logging messages about actions it would have taken, without actually taking any.

  .. code-block:: text

     $ uw jedi run --config-file config.yaml --cycle 2024-05-22T12 --batch --dry-run

.. include:: /shared/key_path.rst

* Specifying the ``--show-schema`` flag, with no other options, prints the driver's schema:

.. literalinclude:: jedi/show-schema.cmd
   :language: text
   :emphasize-lines: 1
.. literalinclude:: jedi/show-schema.out
   :language: text
