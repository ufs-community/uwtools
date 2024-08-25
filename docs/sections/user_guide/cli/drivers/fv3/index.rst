``fv3``
=======

.. include:: ../shared/idempotent.rst

The ``uw`` mode for configuring and running FV3.

.. include:: help.rst

Examples
^^^^^^^^

The examples use a configuration file named ``config.yaml``. Its contents are described in depth in section :ref:`fv3_yaml`. Each of the values in the ``fv3`` YAML may contain Jinja2 variables/expressions using a ``cycle`` variable, which is a Python ``datetime`` object corresponding to the FV3 cycle being run.

* Run FV3 on an interactive node

  .. code-block:: text

     $ uw fv3 run --config-file config.yaml --cycle 2024-02-11T12

  The driver creates a ``runscript.fv3`` file in the directory specified by ``rundir:`` in the config and runs it, executing FV3.

* Run FV3 via a batch job

  .. code-block:: text

     $ uw fv3 run --config-file config.yaml --cycle 2024-02-11T12 --batch

  The driver creates a ``runscript.fv3`` file in the directory specified by ``rundir:`` in the config and submits it to the batch system. Running with ``--batch`` requires a correctly configured ``platform:`` block in ``config.yaml``, as well as appropriate settings in the ``execution:`` block under ``fv3:``.

* Specifying the ``--dry-run`` flag results in the driver logging messages about actions it would have taken, without actually taking any.

  .. code-block:: text

     $ uw fv3 run --config-file config.yaml --cycle 2024-02-11T12 --batch --dry-run

.. include:: /shared/key_path.rst

* The ``run`` task depends on the other available tasks and executes them as prerequisites. It is possible to execute any task directly, which entails execution of any of *its* dependencies. For example, to create an FV3 run directory provisioned with all the files, directories, symlinks, etc. required per the configuration file:

  .. code-block:: text

     $ uw fv3 provisioned_rundir --config-file config.yaml --cycle 2024-02-11T12 --batch

* Specifying the ``--show-schema`` flag, with no other options, prints the driver's schema:

.. literalinclude:: show-schema.cmd
   :language: text
   :emphasize-lines: 1
.. literalinclude:: show-schema.out
   :language: text
