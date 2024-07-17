``cdeps``
=========

The ``uw`` mode for configuring and running the :cdeps:`cdeps<>` component.

.. literalinclude:: cdeps/help.cmd
   :language: text
   :emphasize-lines: 1
.. literalinclude:: cdeps/help.out
   :language: text

All tasks take the same arguments. For example:

.. literalinclude:: cdeps/run-help.cmd
   :language: text
   :emphasize-lines: 1
.. literalinclude:: cdeps/run-help.out
   :language: text

Examples
^^^^^^^^

The examples use a configuration file named ``config.yaml`` with content similar to:

.. highlight:: yaml
.. literalinclude:: /shared/cdeps.yaml

Its contents are described in depth in section :ref:`cdeps_yaml`. Each of the values in the ``cdeps`` YAML may contain Jinja2 variables/expressions using a ``cycle`` variable, which is a Python ``datetime`` object corresponding to the FV3 cycle being run.

TODO: ADD ATM EXAMPLE

* Specifying the ``--dry-run`` flag results in the driver logging messages about actions it would have taken, without actually taking any.

  .. code-block:: text

     $ uw cdeps run --config-file config.yaml --cycle 2023-12-15T18 --batch --dry-run

.. include:: /shared/key_path.rst
