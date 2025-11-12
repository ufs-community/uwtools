``orog_gsl``
============

.. include:: ../shared/idempotent.rst

The ``uw`` mode for configuring and running the UFS Utils preprocessing component ``orog_gsl``. Documentation for this UFS Utils component is :ufs-utils:`here <orog-gsl>`.

.. include:: help.rst

Examples
^^^^^^^^

The examples use a configuration file named ``config.yaml`` with contents similar to:

.. highlight:: yaml
.. literalinclude:: /shared/drivers/orog_gsl.yaml

Its contents are described in section :ref:`orog_gsl_yaml`.

* Run ``orog_gsl`` on an interactive node

  .. code-block:: text

     $ uw orog_gsl run --config-file config.yaml

  The driver creates a ``runscript.orog_gsl`` file in the directory specified by ``rundir:`` in the config and runs it, executing ``orog_gsl``.

* Run ``orog_gsl`` via a batch job

  .. code-block:: text

     $ uw orog_gsl run --config-file config.yaml --batch

  The driver creates a ``runscript.orog_gsl`` file in the directory specified by ``rundir:`` in the config and submits it to the batch system. Running with ``--batch`` requires a correctly configured ``platform:`` block in ``config.yaml``, as well as appropriate settings in the ``execution:`` block under ``orog_gsl:``.

* Specifying the ``--dry-run`` flag results in the driver logging messages about actions it would have taken, without actually taking any.

  .. code-block:: text

     $ uw orog_gsl run --config-file config.yaml --batch --dry-run

.. include:: /shared/key_path.rst

.. include:: schema-options.rst
