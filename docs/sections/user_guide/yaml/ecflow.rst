.. _ecflow_workflows:

ecFlow Workflows
================

:ecflow:`ecFlow<>` is a workflow manager developed by `ECMWF <https://www.ecmwf.int/>`_ and popular in the meteorological community. It defines workflows as suites of tasks with dependencies, resource requirements, and scheduling logic. ecFlow uses a suite definition file (e.g. ``suite.def``) to describe the workflow, and ``ecf`` scripts to carry out individual tasks.

The ``uw ecflow`` tool defines a UW YAML language that can be easily manipulated like any other key-value configuration file and translated into the artifacts required by ecFlow: a suite definition file and, optionally, a set of ``ecf`` scripts.

Top-Level Structure
-------------------

UW YAML for ecFlow nests under a top-level ``ecflow`` key, and the suite definition under a ``suitedef`` child:

.. code-block:: yaml

   ecflow:
     suitedef:
       ...

Suite-Definition Root UW YAML Keys
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The following keys may appear at the top of the suite definition, directly under ``ecflow.suitedef``:

.. code-block:: yaml

   ecflow:
     suitedef:
       extern:
         - /other_suite/family/task
       scheduler: slurm
       suite_forecast:
         ...
       suites_example:
         ...
       vars:
         ECF_HOME: /path/to/ecf
         ACCOUNT: myproject

``extern:``

An optional list of external node paths to declare in the suite definition. Useful for triggering tasks across suites.

``scheduler:``

The batch scheduler to target when generating ``ecf`` scripts. Supported values are ``slurm``, ``pbs``, and ``lsf``. When set, scheduler directives defined in a under ``batchargs:`` in a ``task_<name>`` block are automatically added to generated ``ecf`` scripts. Omit this key if scripts are not needed or if no batch directives are required.

``suite_<name>:``

A suite definition. The portion of the key following ``suite_`` becomes the suite name in ecFlow. For example, ``suite_forecast`` creates a suite named ``forecast``. See `Suite and Node Structure`_ for the contents of a suite.

``suites_<name>:``

An expand block for generating multiple suites from a parameterized template. See `Expand Blocks`_.

.. _ecflow_suite_level_vars:

``vars:``

A mapping of variable name/value pairs set as ecFlow edit variables at the workflow (``Defs``) level. These become globally accessible within the suite.

Variables beginning with ``ECF_`` are reserved by ecFlow and a defined set are supported: :ecflow:`suite definition variables<ug/user_manual/ecflow_variables/ecflow_suite_definition_variables.html>`, and :ecflow:`generated variables<ug/user_manual/ecflow_variables/generated_variables.html>`. Values for the latter are automatically supplied by the ecFlow server for use in ``ecf`` scripts, but can be overriden by users in a suite-definition file.

See the :ecflow:`ecFlow documentation<ug/user_manual/ecflow_variables/index.html>` for more information on available variables and their meanings.

Suite and Node Structure
------------------------

Suites, families, and tasks are defined as nested YAML blocks. Keys are prefixed with ``suite_``, ``family_``, or ``task_`` to indicate their type; the remainder of the key is used as the node name.

.. literalinclude:: /sections/user_guide/cli/tools/ecflow/workflow.yaml
   :language: yaml

This example defines a suite ``workflow`` containing a family ``data_prep`` with tasks ``fetch`` and ``process``, and a top-level task ``run_model``.

  .. include:: /shared/ecflow_task_naming.rst

Node Attributes
^^^^^^^^^^^^^^^

The following attributes may be set on suite, family, or task nodes, at any level in the config hierarchy:

``defstatus:``

Sets the default status of a node (see :ecflow:`ecflow.DState <python_api/DState.html>`). Accepted values are ``complete``, ``suspended``, ``aborted``, ``queued``, ``submitted``, ``active``, and ``unknown``. For example:

.. code-block:: yaml

   task_get_obs:
     defstatus: complete

``events:``

A list of named events attached to a node (see :ecflow:`ecflow.Event <python_api/Event.html>`). Each item may be a string (event name) or a two-element list ``[number, name]``. For example:

.. code-block:: yaml

   task_get_obs:
     events:
       - obs_ready
       - [2, model_ready]

``inlimits:``

A list of limits that a node consumes (see :ecflow:`ecflow.InLimit <python_api/InLimit.html>`). Each item may be a one-, two-, or three-element list ``[limit_name]``, ``[limit_path, limit_name]``, or ``[limit_path, limit_name, tokens]``. For example:

.. code-block:: yaml

   task_run_model:
     inlimits:
       - [/forecast, max_jobs]

``labels:``

A list of label name/value pairs on a node (see :ecflow:`ecflow.Label <python_api/Label.html>`). Each item is a two-element list ``[name, value]``. For example:

.. code-block:: yaml

   task_run_model:
     labels:
       - [progress, "0%"]

``late:``

Defines late notification thresholds for a node (see :ecflow:`ecflow.Late <python_api/Late.html>`). Accepts ``submitted``, ``active``, and ``complete`` as keys, each with a time value. For example:

.. code-block:: yaml

   task_run_model:
     late:
       active: "02:00:00"
       submitted: "00:05:00"

``limits:``

A list of limits defined on a suite or family (see :ecflow:`ecflow.Limit <python_api/Limit.html>`). Each item is a two-element list ``[name, max_count]``. For example:

.. code-block:: yaml

   suite_forecast:
     limits:
       - [max_jobs, 4]

``meters:``

A list of meters on a node (see :ecflow:`ecflow.Meter <python_api/Meter.html>`). Each item is a three- or four-element list ``[name, min, max]`` or ``[name, min, max, threshold]``. For example:

.. code-block:: yaml

   task_run_model:
     meters:
       - [progress, 0, 100]

``trigger:``

A string expression defining the conditions under which a node may run (see :ecflow:`ecflow.Trigger <python_api/Trigger.html>`). Only one ``trigger:`` is allowed per node. For example:

.. code-block:: yaml

   task_run_model:
     trigger: /forecast/prep/get_obs == complete

``vars:``

A mapping of variable name/value pairs to set as ecFlow edit variables on the node (see :ecflow:`ecflow.Variable <python_api/Variable.html>`). For example:

.. code-block:: yaml

   task_run_model:
     vars:
       MEMBER: "001"

See :ref:`this section <ecflow_suite_level_vars>` for more information on ``ECF_`` and other variables that can be set on nodes to override those set at the suite level.

Repeat Attributes
^^^^^^^^^^^^^^^^^

Only one ``repeat_*:`` attribute is allowed per node. The available repeat types are:

``repeat_date:``

Repeats over a date range (see :ecflow:`ecflow.RepeatDate <python_api/RepeatDate.html>`). Requires ``variable``, ``start``, and ``end`` (as YYYYMMDD integers); ``step`` is optional (default 1).

.. code-block:: yaml

   suite_forecast:
     repeat_date:
       variable: YMD
       start: 20240101
       end: 20240131
       step: 1

``repeat_datelist:``

Repeats over an explicit list of dates (see :ecflow:`ecflow.RepeatDateList <python_api/RepeatDateList.html>`) (as YYYYMMDD integers). Requires ``variable`` and ``list``.

``repeat_datetime:``

Repeats over a datetime range (see :ecflow:`ecflow.RepeatDateTime <python_api/RepeatDateTime.html>`). Requires ``variable``, ``start``, and ``end`` (as ``YYYYMMDDTHHmmss`` strings); ``step`` (as ``HH:mm:ss``) is optional.

``repeat_day:``

Repeats by day increment (see :ecflow:`ecflow.RepeatDay <python_api/RepeatDay.html>`). Requires ``step``.

``repeat_enumerated:``

Repeats over an explicit list of strings (see :ecflow:`ecflow.RepeatEnumerated <python_api/RepeatEnumerated.html>`). Requires ``variable`` and ``list``.

``repeat_int:``

Repeats over an integer range (see :ecflow:`ecflow.RepeatInteger <python_api/RepeatInteger.html>`). Requires ``variable``, ``start``, and ``end``; ``step`` is optional.

``repeat_string:``

Repeats over an explicit list of strings (see :ecflow:`ecflow.RepeatString <python_api/RepeatString.html>`). Requires ``variable`` and ``list``.

Task Script Block
-----------------

Tasks are required to have a ``script:`` block that defines the ``ecf`` script to generate. The value of  ``script:`` may be

* A string specifying a path to an ``ecf`` script to be passed verbatim to ecFlow. The script can reference ecFlow ``%<VAR>%`` variables, which will be rendered by the server when converting the ``ecf`` script to a final job script, but must otherwise be complete.

.. code-block:: yaml

   script: /path/to/script.sh

or

* A YAML mapping with the following required and optional keys:

``batchargs:``

Optional. Batch-scheduler directives to add to the ``ecf`` script. See :ref:`this page <batchargs>` for more information.

``body:``

Required. Executable statements for the task. This may be a single command, including the path to a script to execute, or a multiline YAML string specifying a series of statements to execute in a bash shell.

.. code-block:: yaml

   script:
     body: |
       statement1
       statement2
       # etc.

``includes:``

Optional: Subkeys ``entry:`` and ``exit:`` specify sequences of files (typically with ``.h`` extensions) to include before and after the ``body`` statements, respectively, translated to ecFlow ``%include`` statements. By default, include files can be found by the ecFlow server under the directory specified by ``ecflow.server.vars.ECF_HOME`` in the config; this can be overridden by defining ``ecflow.server.vars.ECF_INCLUDE`` (see :ecflow:`here <glossary.html#term-ECF_INCLUDE>`). The include file ``server.h``, which exports several crucial environment variables, is created by ``uw ecflow server`` at startup time and is available for inclusion in application ``ecf`` files.

.. code-block:: yaml

   script:
     includes:
       entry:
       - server.h
       - prep.h
       exit:
       - post.h

In this example ``prep.h`` and ``post.h`` would need to be placed by the application in the ``ECF_HOME`` directory, or in a directory specified by ``ECF_INCLUDE``.

``manual:``

Optional. A brief description of the task's purpose, embedded in the ``ecf`` script's ``%manual`` section. The manual can, for example, be viewed in the :ecflow:`ecFlow GUI <tutorial/getting_started/using-ecflowui.html#using-ecflow-ui>`.

Expand Blocks
-------------

The ``expand:`` mechanism generates multiple nodes from a parameterized template. It is used with the plural forms of node prefixes: ``suites_``, ``families_``, and ``tasks_``.

The ``expand:`` key under a node block defines the variable(s) and their lists of values. The remaining keys in the block are templates rendered once for each element in the expand list, with ``{{ ec.VARNAME }}`` placeholders substituted. All lists under ``expand:`` must have the same length.

.. code-block:: yaml

   ecflow:
     suite_ensemble:
       tasks_member_{{ ec.MEM }}:
         expand:
           MEM: ["01", "02", "03"]
         script:
           execution:
             executable: /path/to/run.sh
             incantation: /path/to/run.sh
           manual: Run ensemble member {{ ec.MEM }}

This expands to three tasks named ``member_01``, ``member_02``, and ``member_03``.

Multiple expand variables of the same length may be provided together:

.. code-block:: yaml

   tasks_member_{{ ec.MEM }}_{{ ec.LABEL }}:
     expand:
       MEM: ["01", "02"]
       LABEL: ["ctrl", "pert"]

Server Configuration
--------------------

The ``uw ecflow server`` command reads configuration from an ``ecflow.server`` block:

.. code-block:: yaml

   ecflow:
     server:
       ECF_HOME: /path/to/run

All keys in the ``server:`` block are passed as environment variables to ``ecflow_server``. Only ``ECF_HOME`` is required. All supported variables, and values accepted by UW YAML for ecFlow, are described :ecflow:`here<glossary.html#term-ecflow_server>`. The lone exception is ``ECF_SSL``, which accepts values as described below.

``ECF_SSL``

Optionally controls SSL for the server. Accepts a boolean or a certificate-filename prefix string:

- ``true`` (default when ``--insecure`` is not given): Enable SSL using the auto-provisioned default certificate triplet (``server.crt`` / ``server.key`` / ``dh2048.pem``) in ``$HOME/.ecflowrc/ssl``.
- A certificate-filename prefix string (e.g. ``myhost.8888``): Enable SSL using the specified certificate files. Files with the given prefix and the extensions ``.crt``, ``.key``, and ``.pem`` must exist under ``$HOME/.ecflowrc/ssl/``.
- ``false``: Disable SSL (equivalent to passing ``--insecure``).

For example, to use a certificate-filename prefix when running on a static port:

.. code-block:: yaml

   ecflow:
     server:
       ECF_SSL: myhost.8888

The ``--port`` value passed to ``uw ecflow server`` must match the port in the prefix. The three files ``myhost.8888.crt``, ``myhost.8888.key``, and ``myhost.8888.pem`` must already exist in ``$HOME/.ecflowrc/ssl``; they are not auto-generated.

When ``--insecure`` is given to ``uw ecflow server``, SSL is disabled entirely regardless of the ``ECF_SSL`` setting.

Generated Artifacts
-------------------

``suite.def``

The ecFlow suite definition file, written to ``<output-path>/suite.def`` if ``--output-path`` is given, otherwise to ``stdout``.

``ecf`` scripts

One ``ecf`` script per task, written under ``<scripts-path>/``. Each script is nested under the ``<scripts-path>`` in the same manner as it is in the suite definition. The example above will output a script at ``<scripts-path>/forecast/prep/get_obs.ecf`` and at ``<scripts-path>/forecast/run_model``, where the script name is derived from the portion of the task name after the first underscore. Scripts are only generated when ``--scripts-path`` is provided to ``uw ecflow realize``.
