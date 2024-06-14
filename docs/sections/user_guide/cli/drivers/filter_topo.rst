``filter_topo``
===============

The ``uw`` mode for configuring and running the UFS Utils preprocessing component ``filter_topo``. Documentation for this UFS Utils component is :ufs-utils:`here <filter-topo>`.

.. literalinclude:: filter_topo/help.cmd
   :language: text
   :emphasize-lines: 1
.. literalinclude:: filter_topo/help.out
   :language: text

All tasks take the same arguments. For example:

.. literalinclude:: filter_topo/run-help.cmd
   :language: text
   :emphasize-lines: 1
.. literalinclude:: filter_topo/run-help.out
   :language: text

Examples
^^^^^^^^

The examples use a configuration file named ``config.yaml`` with contents similar to:

.. highlight:: yaml
.. literalinclude:: /shared/filter_topo.yaml

Its contents are described in section :ref:`filter_topo_yaml`.

* Run ``filter_topo`` on an interactive node

  .. code-block:: text

     $ uw filter_topo run --config-file config.yaml

  The driver creates a ``runscript.filter_topo`` file in the directory specified by ``run_dir:`` in the config and runs it, executing ``filter_topo``.

* Run ``filter_topo`` via a batch job

  .. code-block:: text

     $ uw filter_topo run --config-file config.yaml --batch

  The driver creates a ``runscript.filter_topo`` file in the directory specified by ``run_dir:`` in the config and submits it to the batch system. Running with ``--batch`` requires a correctly configured ``platform:`` block in ``config.yaml``, as well as appropriate settings in the ``execution:`` block under ``filter_topo:``.

* Specifying the ``--dry-run`` flag results in the driver logging messages about actions it would have taken, without actually taking any.

  .. code-block:: text

     $ uw filter_topo run --config-file config.yaml --batch --dry-run

.. include:: /shared/key_path.rst
