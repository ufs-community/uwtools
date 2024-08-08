``execute``
===========

The ``uw`` mode for executing external drivers.

.. literalinclude:: execute/help.cmd
   :language: text
   :emphasize-lines: 1
.. literalinclude:: execute/help.out
   :language: text

.. _cli_execute_examples:
              
Examples
^^^^^^^^

These examples use the following inputs:

Module ``rand.py``

.. literalinclude:: execute/rand.py
   :language: python

Schema ``rand.jsonschema``

.. literalinclude:: execute/rand.jsonschema
     :language: json

Config ``rand.yaml``

.. literalinclude:: execute/rand.yaml
   :language: yaml

* Execute the external driver:

  .. literalinclude:: execute/execute.cmd
     :language: text
     :emphasize-lines: 2
  .. literalinclude:: execute/execute.out
     :language: text
  
* If the external driver does not accept an argument that was provided on the command line, it will exit with error. In this case, ``Rand`` inherits from parent class ``AssetsTimeInvariant``, which does not accept a ``cycle`` argument:

  .. literalinclude:: execute/bad-arg.cmd
     :language: text
     :emphasize-lines: 1
  .. literalinclude:: execute/bad-arg.out
     :language: text
  
* If the schema file for a driver resides in the same directory as its Python module and has the same filename prefix, as well as a ``.jsonschema`` suffix (e.g. ``rand.jsonschema`` alongside ``rand.py``) then the ``--schema-file`` argument is not required. However, ``--schema-file`` can be used to point to an alternate schema:

  .. literalinclude:: execute/alt-schema.cmd
     :language: text
     :emphasize-lines: 2
  .. literalinclude:: execute/alt-schema.out
     :language: text

* Other arguments behave identically to the same-named arguments to built-in ``uwtools`` drivers (see :ref:`drivers`).
