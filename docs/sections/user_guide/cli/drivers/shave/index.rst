``shave``
=========

.. include:: ../shared/idempotent.rst

The ``uw`` mode for configuring and running the UFS Utils preprocessing component ``shave``. Documentation for this UFS Utils component is :ufs-utils:`here <shave>`.

.. include:: help.rst

Examples
^^^^^^^^

The examples use a configuration file named ``config.yaml`` with contents similar to:

.. highlight:: yaml
.. literalinclude:: /shared/shave.yaml

Its contents are described in section :ref:`shave_yaml`.

* Run ``shave`` on an interactive node

  .. code-block:: text

     $ uw shave run --config-file config.yaml

  The driver creates a ``runscript.shave`` file in the directory specified by ``rundir:`` in the config and runs it, executing ``shave``.

* Run ``shave`` via a batch job

  .. code-block:: text

     $ uw shave run --config-file config.yaml --batch

  The driver creates a ``runscript.shave`` file in the directory specified by ``rundir:`` in the config and submits it to the batch system. Running with ``--batch`` requires a correctly configured ``platform:`` block in ``config.yaml``, as well as appropriate settings in the ``execution:`` block under ``shave:``.

* Specifying the ``--dry-run`` flag results in the driver logging messages about actions it would have taken, without actually taking any.

  .. code-block:: text

     $ uw shave run --config-file config.yaml --batch --dry-run

.. include:: /shared/key_path.rst

.. include:: schema-options.rst
