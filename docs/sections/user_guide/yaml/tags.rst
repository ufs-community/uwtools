.. _defining_YAML_tags:

Defining YAML ``tags``
==========================

Tags are used to denote the type of a YAML node when converting to a Python object. Standard YAML tags are defined at http://yaml.org/type/index.html.

Tags may be implicit:

.. code-block:: yaml

   boolean: true
   integer: 3
   float: 3.14

Or explicit:

.. code-block:: yaml

   boolean: !!bool "true"
   integer: !!int "3"
   float: !!float "3.14"

Additionally, UW defines the following tags to support use cases not covered by standard tags:

UW YAML Tags
------------

``!float``
^^^^^^^^^^

Converts the tagged node to a Python ``float`` type.

.. code-block:: yaml

   f2: !float '3.14'


``!int``
^^^^^^^^

Converts the tagged node to a Python ``integer`` type.

.. code-block:: yaml

   cycle_day: !int "{{ cycle.strftime('%d') }}"


``!include``
^^^^^^^^^^^^

Parse the tagged file and include its tags.

.. code-block:: yaml

   salad: !INCLUDE [./fruit_config.yaml]


``!list``
^^^^^^^^^

Converts the tagged node to a Python ``list`` type.

.. code-block:: yaml

   file_names: !list [&gfs_file_names]


``!remove``
^^^^^^^^^^^

Removes the tagged YAML key/value pair.

.. code-block:: yaml

   update_values: !remove
