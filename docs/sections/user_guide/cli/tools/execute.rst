``execute``
===========

The ``uw`` mode for executing external drivers.

.. literalinclude:: execute/help.cmd
   :language: text
   :emphasize-lines: 1
.. literalinclude:: execute/help.out
   :language: text

For the three required arguments:

* ``--module`` specifies the path to a ``.py`` file containing a UW driver class. The path may be: absolute (e.g. ``/path/to/driver.py``), in which case ``uw`` may be invoked from anywhere on the filesystem; relative to the shell's current directory (e.g. ``../driver.py``, ``sub/dir/driver.py``); or simply the filename (e.g. ``driver.py``) if the directory containing the module is added to ``PYTHONPATH``.
* ``--class`` specifies the name of a class in the above module that implements the driver, which should use one of the classes exported by ``uwtools.api.driver`` as its base class.
* ``--task`` specifies the name of a method in the above class that implements a :iotaa:`task<blob/main/README.md#tasks>`, decorated with :iotaa:`@task<blob/main/README.md#task>`, :iotaa:`@tasks<blob/main/README.md#tasks>`, or :iotaa:`@external<blob/main/README.md#external>`.

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
