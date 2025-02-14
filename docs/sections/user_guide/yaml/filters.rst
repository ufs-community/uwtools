Custom Filters
==============

Filters are used to transform values inside Jinja2 expressions. See Jinja2's `general description <https://jinja.palletsprojects.com/en/stable/templates/#filters>`_ or the list of `built-in filters <https://jinja.palletsprojects.com/en/stable/templates/#builtin-filters>`_.

The following custom filters are available from ``uwtools``

``env``
^^^^^^^

Inserts the value of the specified environment variable. For example, given ``config.yaml``

.. code-block:: text

   cycle: "{{ 'CYCLE' | env }}"

and the presence of environment variable ``CYCLE`` with value ``2025021312``:

.. code-block:: text

   $ uw config realize -i config.yaml --output-format yaml
   cycle: '2025021312'

Note that the name of the environment variable must be quoted in the Jinja2 expression so that it is recognized as a string, not a Python variable name.

The ``env`` filter can be combined with :ref:`custom_yaml_tags` to obtain appropriately typed YAML values. For example, give ``config.yaml``

.. code-block:: text

   leadtime: !int "{{ 'LEADTIME' | env }}"

and the presence of environment variable ``LEADTIME`` with value ``6``:

.. code-block:: text

   $ uw config realize -i config.yaml --output-format yaml
   leadtime: 6

Note that ``6`` here is a YAML integer, not a string, and will be instantiated in Python as an ``int``.
