.. _custom_yaml_tags:

Custom Tags
===========

Tags are used to denote the type of a YAML node when converting to a Python object.

UW supports the use of standard YAML tags, denoted by `!!` as defined `here <http://yaml.org/type/index.html>`_. Additionally, UW defines the following tags to support use cases not covered by standard tags, denoted by `!` and described in detail below. Where standard YAML tags are applied to their values immediately, application of UW YAML tags is delayed until after Jinja2 expressions in tagged values are dereferenced.

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

**NB** Values tagged with UW YAML tags must be strings. Use quotes as necessary to ensure that they are.

``!bool``
^^^^^^^^^

Converts the tagged node to a Python ``bool`` object. For example, given ``input.yaml``:

.. code-block:: yaml

   flag1: True
   flag2: !bool "{{ flag1 }}"
   flag3: !bool "0"

.. code-block:: text

   $ uw config realize -i ../input.yaml --output-format yaml
   flag1: True
   flag2: True
   flag3: False


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

``!dict``
^^^^^^^^^

Converts the tagged node to a Python ``dict`` value. For example, given ``input.yaml``:

.. code-block:: yaml

   d1: {'k0': 0, 'k1': 1, 'k2': 2}
   d2: !dict "{ k0: 0, k1: 1, k2: 2 }"
   d3: !dict "{{ '{' }}{% for n in range(3) %} k{{ n }}:{{ n }},{% endfor %}{{ '}' }}"
   d4: !dict "[{% for n in range(3) %}[k{{ n }},{{ n }}],{% endfor %}]"

.. code-block:: text

   $ uw config realize --input-file input.yaml --output-format yaml
   d1: {'k0': 0, 'k1': 1, 'k2': 2}
   d2: {'k0': 0, 'k1': 1, 'k2': 2}
   d3: {'k0': 0, 'k1': 1, 'k2': 2}
   d4: {'k0': 0, 'k1': 1, 'k2': 2}

``!float``
^^^^^^^^^^

Converts the tagged node to a Python ``float`` value. For example, given ``input.yaml``:

.. code-block:: yaml

   f2: !float "{{ 3.141 + 2.718 }}"

.. code-block:: text

   $ uw config realize --input-file input.yaml --output-format yaml
   f2: 5.859

``!glob``
^^^^^^^^^

Only for use in :ref:`File Blocks<files_yaml>`. See :ref:`Glob Support<files_yaml_glob_support>` for more information.

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

Values from files later in the sequence overwrite their predecessors, and full-value replacement, not structural merging, is performed. For example, given ``numbers.yaml``:

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

``!list``
^^^^^^^^^

Converts the tagged node to a Python ``list`` value. For example, given ``input.yaml``:

.. code-block:: yaml

   l1: [1, 2, 3]
   l2: !list "[{% for n in range(3) %} a{{ n }},{% endfor %} ]"
   l3: !list "[ a0, a1, a2, ]"

.. code-block:: text

   $ uw config realize --input-file input.yaml --output-format yaml
   l1: [1, 2, 3]
   l2: ['a0', 'a1', 'a2']
   l3: ['a0', 'a1', 'a2']

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
