.. _defining_YAML_tags:

UW YAML tags
============

Tags are used to denote the type of a YAML node when converting to a Python object. Standard YAML tags are defined `here <http://yaml.org/type/index.html>`_.

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

``!datetime``
^^^^^^^^^^^^^

Converts the tagged node to a Python ``datetime`` object. For example, given ``input.yaml``:

.. code-block:: yaml

   date1: 2024-09-01
   date2: !datetime "{{ date1 }}"

.. code-block:: text

   % uw config realize -i ../input.yaml --output-format yaml
   date1: 2024-09-01
   date2: 2024-09-01 00:00:00

The value provided to the tag must be in ISO 8601 format to be interpreted correctly by the ``!datetime`` tag.

``!float``
^^^^^^^^^^

Converts the tagged node to a Python ``float`` value. For example, given ``input.yaml``:

.. code-block:: yaml

   f2: !float "{{ 3.141 + 2.718 }}"

.. code-block:: text

   % uw config realize --input-file input.yaml --output-format yaml
   f2: 5.859

``!int``
^^^^^^^^

Converts the tagged node to a Python ``int`` value. For example, given ``input.yaml``:

.. code-block:: yaml

   f1: 3
   f2: 11
   f3: !int "{{ (f1 + f2) * 10 }}"

.. code-block:: text

   % uw config realize --input-file input.yaml --output-format yaml
   f1: 3
   f2: 11
   f2: 140

``!include``
^^^^^^^^^^^^

Parse the tagged file and include its tags. For example, given ``input.yaml``:

.. code-block:: yaml

   values: !include [./supplemental.yaml]

and ``supplemental.yaml``:

.. code-block:: yaml

   e: 2.718
   pi: 3.141

.. code-block:: text

   % uw config realize --input-file input.yaml --output-format yaml
   values:
      e: 2.718
      pi: 3.141

``!remove``
^^^^^^^^^^^

Removes the tagged YAML key/value pair. For example, given ``input.yaml``:

.. code-block:: yaml

   e: 2.718
   pi: 3.141

and ``update.yaml``:

.. code-block:: yaml

   e: !remove

.. code-block:: text

   % uw config realize --input-file input.yaml --update-file update.yaml --output-format yaml
   pi: 3.141
