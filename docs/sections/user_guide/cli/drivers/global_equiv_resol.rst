``global_equiv_resol``
======================

.. include:: /shared/idempotent.rst

The ``uw`` mode for configuring and running the UFS Utils preprocessing component ``global_equiv_resol``. Documentation for this UFS Utils component is :ufs-utils:`here <global-equiv-resol>`.

.. literalinclude:: global_equiv_resol/help.cmd
   :language: text
   :emphasize-lines: 1
.. literalinclude:: global_equiv_resol/help.out
   :language: text

All tasks take the same arguments. For example:

.. literalinclude:: global_equiv_resol/run-help.cmd
   :language: text
   :emphasize-lines: 1
.. literalinclude:: global_equiv_resol/run-help.out
   :language: text

Examples
^^^^^^^^

The examples use a configuration file named ``config.yaml`` with contents similar to:

.. highlight:: yaml
.. literalinclude:: /shared/global_equiv_resol.yaml

Its contents are described in section :ref:`global_equiv_resol_yaml`.

* Run ``global_equiv_resol`` on an interactive node

  .. code-block:: text

     $ uw global_equiv_resol run --config-file config.yaml

  The driver creates a ``runscript.global_equiv_resol`` file in the directory specified by ``rundir:`` in the config and runs it, executing ``global_equiv_resol``.

* Run ``global_equiv_resol`` via a batch job

  .. code-block:: text

     $ uw global_equiv_resol run --config-file config.yaml --batch

  The driver creates a ``runscript.global_equiv_resol`` file in the directory specified by ``rundir:`` in the config and submits it to the batch system. Running with ``--batch`` requires a correctly configured ``platform:`` block in ``config.yaml``, as well as appropriate settings in the ``execution:`` block under ``global_equiv_resol:``.

* Specifying the ``--dry-run`` flag results in the driver logging messages about actions it would have taken, without actually taking any.

  .. code-block:: text

     $ uw global_equiv_resol run --config-file config.yaml --batch --dry-run

.. include:: /shared/key_path.rst
