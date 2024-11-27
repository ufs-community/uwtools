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

``!bool``
^^^^^^^^^

Converts the tagged node to a Python ``bool`` object. For example, given ``input.yaml``:

.. code-block:: yaml

   flag1: True
   flag2: !bool "{{ flag1 }}"

.. code-block:: text

   $ uw config realize -i ../input.yaml --output-format yaml
   flag1: True
   flag2: True


``!datetime``
^^^^^^^^^^^^^

Converts the tagged node to a Python ``datetime`` object. For example, given ``input.yaml``:

.. code-block:: yaml

   date1: 2024-09-01
   date2: !datetime "{{ date1 }}"

.. code-block:: text

   $ uw config realize -i ../input.yaml --output-format yaml
   date1: 2024-09-01
   date2: 2024-09-01 00:00:00

The value provided to the tag must be in :python:`ISO 8601 format<datetime.html#datetime.datetime.fromisoformat>` to be interpreted correctly by the ``!datetime`` tag.

``!float``
^^^^^^^^^^

Converts the tagged node to a Python ``float`` value. For example, given ``input.yaml``:

.. code-block:: yaml

   f2: !float "{{ 3.141 + 2.718 }}"

.. code-block:: text

   $ uw config realize --input-file input.yaml --output-format yaml
   f2: 5.859

``!include``
^^^^^^^^^^^^

Load and parse the files specified in the tagged sequence value and insert their contents here. For example, given ``numbers.yaml``:

.. code-block:: yaml

   values: !include [constants.yaml]

and ``constants.yaml``:

.. code-block:: yaml

   e: 2.718
   pi: 3.141

.. code-block:: text

   $ uw config realize --input-file numbers.yaml --output-format yaml
   values:
     e: 2.718
     pi: 3.141

Values from files later in the sequence overwrite their predecessors, and full-value replacement, not structural merging, is performed. For example, giben ``numbers.yaml``:

.. code-block:: yaml

   values: !include [e.yaml, pi.yaml]

``e.yaml``:

.. code-block:: yaml

   constants:
     e: 2.718

and ``pi.yaml``:

.. code-block:: yaml

   constants:
     pi: 3.141

.. code-block:: text

   $ uw config realize --input-file numbers.yaml --output-format yaml
   values:
     constants:
       pi: 3.141

``!int``
^^^^^^^^

Converts the tagged node to a Python ``int`` value. For example, given ``input.yaml``:

.. code-block:: yaml

   f1: 3
   f2: 11
   f3: !int "{{ (f1 + f2) * 10 }}"

.. code-block:: text

   $ uw config realize --input-file input.yaml --output-format yaml
   f1: 3
   f2: 11
   f2: 140

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

   $ uw config realize --input-file input.yaml --update-file update.yaml --output-format yaml
   pi: 3.141
