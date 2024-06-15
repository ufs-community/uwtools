``make_hgrid``
==============

The ``uw`` mode for configuring and running the UFS Utils preprocessing component ``make_hgrid``. Documentation for this UFS Utils component is :ufs-utils:`here <make-hgrid>`.

.. literalinclude:: make_hgrid/help.cmd
   :language: text
   :emphasize-lines: 1
.. literalinclude:: make_hgrid/help.out
   :language: text

All tasks take the same arguments. For example:

.. literalinclude:: make_hgrid/run-help.cmd
   :language: text
   :emphasize-lines: 1
.. literalinclude:: make_hgrid/run-help.out
   :language: text

Examples
^^^^^^^^

The examples use a configuration file named ``config.yaml`` with contents similar to:

.. highlight:: yaml
.. literalinclude:: /shared/make_hgrid.yaml

Its contents are described in section :ref:`make_hgrid_yaml`.

* Run ``make_hgrid`` on an interactive node

  .. code-block:: text

     $ uw make_hgrid run --config-file config.yaml

  The driver creates a ``runscript.make_hgrid`` file in the directory specified by ``run_dir:`` in the config and runs it, executing ``make_hgrid``.

  An example runscript:

  .. literalinclude:: make_hgrid/runscript.cmd
     :language: text
     :emphasize-lines: 5
  .. literalinclude:: make_hgrid/runscript.out
     :language: text

* Run ``make_hgrid`` via a batch job

  .. code-block:: text

     $ uw make_hgrid run --config-file config.yaml --batch

  The driver creates a ``runscript.make_hgrid`` file in the directory specified by ``run_dir:`` in the config and submits it to the batch system. Running with ``--batch`` requires a correctly configured ``platform:`` block in ``config.yaml``, as well as appropriate settings in the ``execution:`` block under ``make_hgrid:``.

* Specifying the ``--dry-run`` flag results in the driver logging messages about actions it would have taken, without actually taking any.

  .. code-block:: text

     $ uw make_hgrid run --config-file config.yaml --batch --dry-run

.. include:: /shared/key_path.rst
