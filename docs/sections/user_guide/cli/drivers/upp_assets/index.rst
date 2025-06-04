``upp_assets``
==============

.. include:: ../shared/idempotent.rst

The ``uw`` mode for configuring the `UPP <https://epic.noaa.gov/unified-post-processor/>`_ component. This driver provisions required assets for UPP under the assumption that it will be executed by another process.

.. include:: help.rst

Examples
^^^^^^^^

The examples use a configuration file named ``config.yaml`` with contents similar to:

.. highlight:: yaml
.. literalinclude:: /shared/upp_assets.yaml

Its contents are described in depth in section :ref:`upp_assets_yaml`.

* Provision assets for execution of UPP by another process

  .. code-block:: text

     $ uw upp_assets provisioned_rundir --config-file config.yaml --cycle 2024-05-06T12 --leadtime 6

* Specifying the ``--dry-run`` flag results in the driver logging messages about actions it would have taken, without actually taking any.

  .. code-block:: text

     $ uw upp_assets provisioned_rundir --config-file config.yaml --cycle 2024-05-06T12 --leadtime 6 --dry-run

.. include:: /shared/key_path.rst

.. include:: schema-options.rst
