``cdeps``
=========

.. include:: ../shared/idempotent.rst

The ``uw`` mode for configuring and running the :CDEPS:`cdeps<>` component.

.. include:: help.rst

Examples
^^^^^^^^

The examples use a configuration file named ``config.yaml`` with content similar to:

.. highlight:: yaml
.. literalinclude:: /shared/cdeps.yaml

Its contents are described in depth in section :ref:`cdeps_yaml`. Each of the values in the ``cdeps`` YAML may contain Jinja2 variables/expressions using a ``cycle`` variable, which is a Python ``datetime`` object corresponding to the FV3 cycle being run.

* Create CDEPS atm configuration:

  .. code-block:: text

     $ uw cdeps atm --config-file config.yaml --cycle 2023-12-15T18

  The driver creates a ``datm_in`` Fortran namelist file and a ``datm.streams`` stream-configuration file in the directory specified by ``rundir:`` in the config.

* Specifying the ``--dry-run`` flag results in the driver logging messages about actions it would have taken, without actually taking any.

  .. code-block:: text

     $ uw cdeps run --config-file config.yaml --cycle 2023-12-15T18 --batch --dry-run

.. include:: /shared/key_path.rst

.. include:: schema-options.rst
