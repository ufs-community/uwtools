* The ``--key-path`` option can be used to navigate from the top of the config to the driver's configuration block. For example, specifying ``--key-path foo.bar`` with config

.. highlight:: yaml
.. literalinclude:: /shared/key_path_nested.yaml

is equivalent to using config

.. highlight:: yaml
.. literalinclude:: /shared/key_path_simple.yaml

without specifying ``--key-path``.
