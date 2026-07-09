``ecflow``
==========

.. contents::
   :backlinks: top
   :depth: 1
   :local:

The ``uw`` mode for realizing and validating ecFlow suite definitions.

.. literalinclude:: ecflow/help.cmd
   :language: text
   :emphasize-lines: 1
.. literalinclude:: ecflow/help.out
   :language: text

.. _cli_ecflow_realize_examples:

``realize``
-----------

In ``uw`` terminology, to ``realize`` a configuration file is to transform it from its raw form into its final, usable state. In the case of ``uw ecflow``, that means transforming a structured UW YAML file into an :ecflow:`ecFlow<>` suite definition file (``suite.def``) and, optionally, a set of ``ecf`` scripts. The structured YAML language required by UW closely follows the concepts defined by ecFlow.

See :ref:`ecflow_workflows` for more information about the structured UW YAML for ecFlow.

.. literalinclude:: ecflow/realize-help.cmd
   :language: text
   :emphasize-lines: 1
.. literalinclude:: ecflow/realize-help.out
   :language: text

Examples
^^^^^^^^

The examples in this section use a UW YAML file ``forecast.yaml`` with contents:

.. literalinclude:: ecflow/forecast.yaml
   :language: yaml

* To realize a UW YAML input file to ``stdout`` in ecFlow suite definition format:

  .. literalinclude:: ecflow/realize-exec-stdout.cmd
     :language: text
     :emphasize-lines: 1
  .. literalinclude:: ecflow/realize-exec-stdout.out
     :language: text

* To realize a UW YAML input file to a directory (writes ``suite.def`` inside that directory):

  .. literalinclude:: ecflow/realize-exec-dir.cmd
     :language: text
     :emphasize-lines: 2
  .. literalinclude:: ecflow/realize-exec-dir.out
     :language: text

* To read the UW YAML from ``stdin`` and write the suite definition to ``stdout``:

  .. literalinclude:: ecflow/realize-exec-stdin-stdout.cmd
     :language: text
     :emphasize-lines: 1
  .. literalinclude:: ecflow/realize-exec-stdin-stdout.out
     :language: text

* To also generate ``ecf`` scripts, using a UW YAML file ``workflow.yaml`` with contents:

  .. literalinclude:: ecflow/workflow.yaml
     :language: yaml

  .. literalinclude:: ecflow/realize-exec-scripts.cmd
     :language: text
     :emphasize-lines: 1
  .. literalinclude:: ecflow/realize-exec-scripts.out
     :language: text

  The ``--scripts-path`` option specifies the directory under which ``ecf`` scripts are written. Each script is placed at the same nested subdirectory level under ``<scripts-path>`` as dictated by the nesting level of the task node in the suite definition. For the example above, the generated scripts are:

  * ``workflow_output/workflow/data_prep/fetch.ecf``:

    .. literalinclude:: ecflow/workflow_output/workflow/data_prep/fetch.ecf
       :language: bash

  * ``workflow_output/workflow/data_prep/process.ecf``:

    .. literalinclude:: ecflow/workflow_output/workflow/data_prep/process.ecf
       :language: bash

  * ``workflow_output/workflow/model.ecf``:

    .. literalinclude:: ecflow/workflow_output/workflow/model.ecf
       :language: bash

  .. important::

    **Task Naming Convention**: Task keys must follow the pattern ``task_<name>``. When ``ecf`` scripts are generated, the ``<name>`` portion becomes the script filename with a ``.ecf`` extension. See :ref:`ecflow_workflows` for more information about the structured UW YAML for ecFlow.

     Examples:

     - ``task_fetch`` → ``fetch.ecf``
     - ``task_run_model`` → ``model.ecf``
     - ``task_process_output_files`` → ``process_output_files.ecf``

.. _cli_ecflow_server_examples:

``server``
----------

.. literalinclude:: ecflow/server-help.cmd
   :language: text
   :emphasize-lines: 1
.. literalinclude:: ecflow/server-help.out
   :language: text

Examples
^^^^^^^^

* To start a server on a random available port with SSL security:

  .. code-block:: text

     uw ecflow server --config-file server.yaml

* To start a server on a specific port:

  .. code-block:: text

     uw ecflow server --config-file server.yaml --port 54321

* To start a server using a named certificate triplet:

  .. code-block:: text

     uw ecflow server --config-file server.yaml --port 8888

  Where ``server.yaml`` contains:

  .. code-block:: yaml

     ecflow:
       server:
         ECF_HOME: /path/to/run
         ECF_SSL: myhost.8888

  ``ECF_SSL`` accepts ``true`` to enable SSL using the default certificate triplet (``server.crt`` / ``server.key`` / ``dh2048.pem``) in ``$HOME/.ecflowrc/ssl``, or a ``<host>.<port>`` prefix string to select a named certificate triplet (``<host>.<port>.crt`` / ``.key`` / ``.pem``) from the same directory. The ``--port`` value must match the port in the prefix when using a named triplet. See :ref:`ecflow_workflows` for full server YAML documentation.

* To emit a JSON report of the server details to ``stdout``:

  .. code-block:: text

     uw ecflow server --config-file server.yaml --report

  The ``--report`` switch prints the ecFlow connection variables, ready to be consumed by downstream tooling (e.g. merged into a UW YAML for ``uw ecflow realize``):

  .. code-block:: json

     {
       "vars": {
         "ECF_HOME": "/path/to/run",
         "ECF_HOST": "server.hostname.com",
         "ECF_PORT": "8888",
         "ECF_SSL": "myhost.8888"
       }
     }

  ``ECF_SSL`` is included only when SSL security is enabled (i.e. when ``--insecure`` is not given and ``ECF_SSL`` is not ``false`` in the config).

.. _cli_ecflow_validate_examples:

``validate``
------------

.. literalinclude:: ecflow/validate-help.cmd
   :language: text
   :emphasize-lines: 1
.. literalinclude:: ecflow/validate-help.out
   :language: text

Examples
^^^^^^^^

The examples in this section use the UW YAML file ``forecast.yaml`` shown above.

* To validate a UW YAML config file:

  .. literalinclude:: ecflow/validate-good-file.cmd
     :language: text
     :emphasize-lines: 1
  .. literalinclude:: ecflow/validate-good-file.out
     :language: text

* To validate a UW YAML config from ``stdin``:

  .. literalinclude:: ecflow/validate-good-stdin.cmd
     :language: text
     :emphasize-lines: 1
  .. literalinclude:: ecflow/validate-good-stdin.out
     :language: text

* When the config is invalid:

  In this example, the top-level ``ecflow:`` key is missing.

  .. literalinclude:: ecflow/validate-bad-file.cmd
     :language: text
     :emphasize-lines: 1
  .. literalinclude:: ecflow/validate-bad-file.out
     :language: text
