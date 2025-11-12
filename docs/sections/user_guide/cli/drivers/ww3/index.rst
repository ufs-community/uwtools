``ww3``
=======

.. include:: ../shared/idempotent.rst

The ``uw`` mode for configuring and running the :ww3:`Wave Watch III<>` component.

.. include:: help.rst

Examples
^^^^^^^^

The examples use a configuration file named ``config.yaml`` with content similar to:

.. highlight:: yaml
.. literalinclude:: /shared/drivers/ww3.yaml

Its contents are described in depth in section :ref:`ww3_yaml`. A Python ``datetime`` object named ``cycle`` is available for use in Jinja2 variables/expressions in the config.

* Create a provisioned run directory:

  .. code-block:: text

     $ uw ww3 provisioned_rundir --config-file config.yaml --cycle 2024-10-21T12

* Validate the config file:

  .. code-block:: text

     $ uw ww3 validate --config-file config.yaml --cycle 2024-10-21T12

.. include:: /shared/key_path.rst

.. include:: schema-options.rst
