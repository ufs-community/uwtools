``chgres_cube``
===============

.. include:: /shared/idempotent.rst

The ``uw`` mode for configuring and running the :ufs-utils:`chgres_cube<chgres-cube>` component.

.. literalinclude:: chgres_cube/help.cmd
   :language: text
   :emphasize-lines: 1
.. literalinclude:: chgres_cube/help.out
   :language: text

All tasks take the same arguments. For example:

.. literalinclude:: chgres_cube/run-help.cmd
   :language: text
   :emphasize-lines: 1
.. literalinclude:: chgres_cube/run-help.out
   :language: text

Examples
^^^^^^^^

The examples use a configuration file named ``config.yaml`` with content similar to:

.. highlight:: yaml
.. literalinclude:: /shared/chgres_cube.yaml

Its contents are described in depth in section :ref:`chgres_cube_yaml`. Each of the values in the ``chgres_cube`` YAML may contain Jinja2 variables/expressions using a ``cycle`` variable, which is a Python ``datetime`` object corresponding to the FV3 cycle being run.

* Run ``chgres_cube`` on an interactive node

  .. code-block:: text

     $ uw chgres_cube run --config-file config.yaml --cycle 2023-12-15T18

  The driver creates a ``runscript.chgres_cube`` file in the directory specified by ``rundir:`` in the config and runs it, executing ``chgres_cube``.

* Run ``chgres_cube`` via a batch job

  .. code-block:: text

     $ uw chgres_cube run --config-file config.yaml --cycle 2023-12-15T18 --batch

  The driver creates a ``runscript.chgres_cube`` file in the directory specified by ``rundir:`` in the config and submits it to the batch system. Running with ``--batch`` requires a correctly configured ``platform:`` block in ``config.yaml``, as well as appropriate settings in the ``execution:`` block under ``chgres_cube:``.

* Specifying the ``--dry-run`` flag results in the driver logging messages about actions it would have taken, without actually taking any.

  .. code-block:: text

     $ uw chgres_cube run --config-file config.yaml --cycle 2023-12-15T18 --batch --dry-run

.. include:: /shared/key_path.rst

* The ``run`` task depends on the other available tasks and executes them as prerequisites. It is possible to execute any task directly, which entails execution of any of *its* dependencies. For example, to create a ``chgres_cube`` run directory provisioned with all the files, directories, symlinks, etc. required per the configuration file:

  .. code-block:: text

     $ uw chgres_cube provisioned_rundir --config-file config.yaml --cycle 2023-12-15T18 --batch
