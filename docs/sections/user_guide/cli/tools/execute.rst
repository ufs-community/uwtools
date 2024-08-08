``execute``
===========

The ``uw`` mode for executing external drivers.

.. literalinclude:: execute/help.cmd
   :language: text
   :emphasize-lines: 1
.. literalinclude:: execute/help.out
   :language: text

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
  
