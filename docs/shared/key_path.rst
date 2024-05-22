The ``--key-path`` option can be used to navigate from the top of the config to the driver's configuration block. For example, specifying ``--key-path foo.bar`` with config

.. literalinclude:: key_path_nested.yaml
.. highlight:: yaml

is equivalent to using config

.. literalinclude:: key_path_simple.yaml
.. highlight:: yaml

without specifying ``--key-path``.
