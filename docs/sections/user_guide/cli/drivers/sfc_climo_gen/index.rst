``sfc_climo_gen``
=================

.. include:: ../shared/idempotent.rst

The ``uw`` mode for configuring and running the :sfc-climo-gen:`sfc_climo_gen<>` component.

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
.. literalinclude:: /shared/sfc_climo_gen.yaml

Its contents are described in depth in section :ref:`sfc_climo_gen_yaml`.

* Run ``sfc_climo_gen`` on an interactive node

  .. code-block:: text

     $ uw sfc_climo_gen run --config-file config.yaml

  The driver creates a ``runscript.sfc_climo_gen`` file in the directory specified by ``rundir:`` in the config and runs it, executing ``sfc_climo_gen``.

* Run ``sfc_climo_gen`` via a batch job

  .. code-block:: text

     $ uw sfc_climo_gen run --config-file config.yaml --batch

  The driver creates a ``runscript.sfc_climo_gen`` file in the directory specified by ``rundir:`` in the config and submits it to the batch system. Running with ``--batch`` requires a correctly configured ``platform:`` block in ``config.yaml``, as well as appropriate settings in the ``execution:`` block under ``sfc_climo_gen:``.

* Specifying the ``--dry-run`` flag results in the driver logging messages about actions it would have taken, without actually taking any.

  .. code-block:: text

     $ uw sfc_climo_gen run --config-file config.yaml --batch --dry-run

.. include:: /shared/key_path.rst

* The ``run`` task depends on the other available tasks and executes them as prerequisites. It is possible to execute any task directly, which entails execution of any of *its* dependencies. For example, to create an ``sfc_climo_gen`` run directory provisioned with all the files, directories, symlinks, etc. required per the configuration file:

  .. code-block:: text

     $ uw sfc_climo_gen provisioned_rundir --config-file config.yaml --batch

* Specifying the ``--show-schema`` flag, with no other options, prints the driver's schema:

.. literalinclude:: show-schema.cmd
   :language: text
   :emphasize-lines: 1
.. literalinclude:: show-schema.out
   :language: text
