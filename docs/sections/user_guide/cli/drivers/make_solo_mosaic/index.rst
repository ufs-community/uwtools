``make_solo_mosaic``
====================

.. include:: /shared/idempotent.rst

The ``uw`` mode for configuring and running the UFS Utils preprocessing component ``make_solo_mosaic``. Documentation for this UFS Utils component is :ufs-utils:`here <make-solo-mosaic>`.

.. literalinclude:: help.cmd
   :language: text
   :emphasize-lines: 1
.. literalinclude:: help.out
   :language: text

All tasks take the same arguments. For example:

.. literalinclude:: run-help.cmd
   :language: text
   :emphasize-lines: 1
.. literalinclude:: run-help.out
   :language: text

Examples
^^^^^^^^

The examples use a configuration file named ``config.yaml`` with contents similar to:

.. highlight:: yaml
.. literalinclude:: /shared/make_solo_mosaic.yaml

Its contents are described in section :ref:`make_solo_mosaic_yaml`.

* Run ``make_solo_mosaic`` on an interactive node

  .. code-block:: text

     $ uw make_solo_mosaic run --config-file config.yaml

  The driver creates a ``runscript.make_solo_mosaic`` file in the directory specified by ``rundir:`` in the config and runs it, executing ``make_solo_mosaic``.

..
  An example runscript:

  .. literalinclude:: runscript.cmd
     :language: text
     :emphasize-lines: 5
  .. literalinclude:: runscript.out
     :language: text

* Run ``make_solo_mosaic`` via a batch job

  .. code-block:: text

     $ uw make_solo_mosaic run --config-file config.yaml --batch

  The driver creates a ``runscript.make_solo_mosaic`` file in the directory specified by ``rundir:`` in the config and submits it to the batch system. Running with ``--batch`` requires a correctly configured ``platform:`` block in ``config.yaml``, as well as appropriate settings in the ``execution:`` block under ``make_solo_mosaic:``.

* Specifying the ``--dry-run`` flag results in the driver logging messages about actions it would have taken, without actually taking any.

  .. code-block:: text

     $ uw make_solo_mosaic run --config-file config.yaml --batch --dry-run

.. include:: /shared/key_path.rst

* Specifying the ``--show-schema`` flag, with no other options, prints the driver's schema:

.. literalinclude:: show-schema.cmd
   :language: text
   :emphasize-lines: 1
.. literalinclude:: show-schema.out
   :language: text
