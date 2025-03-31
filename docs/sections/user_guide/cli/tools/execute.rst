``execute``
===========

The ``uw`` mode for executing external drivers.

.. literalinclude:: execute/help.cmd
   :language: text
   :emphasize-lines: 1
.. literalinclude:: execute/help.out
   :language: text

For the three required arguments:

* ``--module`` specifies the name of the module providing the driver. The name may be an absolute path (e.g. ``/path/to/driver.py``); a path relative to the current directory (e.g. ``driver.py``, ``../driver.py``, ``sub/dir/driver.py``); or a name appropriate to the Python ``import`` statement (e.g. ``driver``, ``my.package.driver``), provided the directory containing the module is on ``PYTHONPATH`` / ``sys.path``.
* ``--class`` specifies the name of a class in the above module that implements the driver, which should use one of the classes exported by ``uwtools.api.driver`` as its base class.
* ``--task`` specifies the name of a method in the above class that implements a :iotaa-readme:`task<tasks>`, decorated with :iotaa-readme:`@task<task>`, :iotaa-readme:`@tasks<tasks-1>`, or :iotaa-readme:`@external<external>`.

.. _cli_execute_examples:
              
Examples
^^^^^^^^

These examples use the following inputs:

Module ``answer.py``

.. literalinclude:: execute/answer.py
   :language: python

Schema ``answer.jsonschema``

.. literalinclude:: execute/answer.jsonschema
     :language: json

Config ``answer.yaml``

.. literalinclude:: execute/answer.yaml
   :language: yaml

* Execute the external driver:

  .. literalinclude:: execute/execute.cmd
     :language: text
     :emphasize-lines: 2
  .. literalinclude:: execute/execute.out
     :language: text
  
* If the external driver does not accept an argument that was provided on the command line, it will exit with error. In this case, ``Answer`` inherits from parent class ``AssetsTimeInvariant``, which does not accept a ``cycle`` argument:

  .. literalinclude:: execute/bad-arg.cmd
     :language: text
     :emphasize-lines: 1
  .. literalinclude:: execute/bad-arg.out
     :language: text
  
* If the schema file for a driver resides in the same directory as its Python module and has the same filename prefix, as well as a ``.jsonschema`` suffix (e.g. ``answer.jsonschema`` alongside ``answer.py``) then the ``--schema-file`` argument is not required. However, ``--schema-file`` can be used to point to an alternate schema:

  .. literalinclude:: execute/answer-alt.cmd
     :language: text
     :emphasize-lines: 2
  .. literalinclude:: execute/answer-alt.out
     :language: text

* Other arguments behave identically to the same-named arguments to internal ``uwtools`` drivers (see :ref:`drivers`).
