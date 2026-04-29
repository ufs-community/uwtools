.. _ecflow_workflows:

ecFlow Workflows
================

:ecflow:`ecFlow<>` is a workflow manager used by :ufs:`UFS<>` users and developers. It defines workflows as suites of tasks with dependencies, resource requirements, and scheduling logic. ecFlow uses a suite definition file (``suite.def``) to describe the workflow, and ecf scripts (``*.ecf``) to carry out individual tasks.

The ``uw ecflow`` tool defines a UW YAML language that can be easily manipulated like any other key/value configuration file and translates it into the artifacts required by ecFlow: a suite definition file and, optionally, a set of ecf scripts.

Top-Level Structure
-------------------

The UW YAML config for ecFlow must have a top-level ``ecflow:`` key:

.. code-block:: yaml

   ecflow:
     scheduler: slurm
     suite_forecast:
       ...

UW YAML Keys
^^^^^^^^^^^^

``scheduler:`` -- Optional. The batch scheduler to use when generating ecf scripts. Supported values are ``lsf``, ``pbs``, and ``slurm``. When set, the scheduler's directives are automatically added to generated ecf scripts. Omit this key if scripts are not needed or if no batch directives are required.

``vars:`` -- Optional. A mapping of variable name/value pairs set as ecFlow edit variables at the workflow (``Defs``) level. These become globally accessible within the suite. For example:

.. code-block:: yaml

   ecflow:
     vars:
       ECF_HOME: /path/to/ecf
       ACCOUNT: myproject

``extern:`` -- Optional. A list of external node paths to declare in the suite definition. Useful for triggering tasks across suites. For example:

.. code-block:: yaml

   ecflow:
     extern:
       - /other_suite/family/task

``suite_<name>:`` -- One or more suite definitions. The portion of the key following ``suite_`` becomes the suite name in ecFlow. For example, ``suite_forecast`` creates a suite named ``forecast``. See `Suite and Node Structure`_ for the contents of a suite.

``suites_<name>:`` -- An expand block for generating multiple suites from a parameterized template. See `Expand Blocks`_.

Suite and Node Structure
------------------------

Suites, families, and tasks are defined as nested YAML blocks. Keys are prefixed with ``suite_``, ``family_``, or ``task_`` to indicate their type; the remainder of the key is used as the node name.

.. code-block:: yaml

   ecflow:
     suite_forecast:
       family_prep:
         task_get_obs:
           trigger: "1==1"
           script:
             execution:
               executable: uw fs get_obs.yaml
               jobcmd: /path/to/run_get_obs.sh
             manual: Retrieve observation data
       task_run_model:
         trigger: /forecast/prep/get_obs == complete
         script:
           execution:
             executable: model.exe
             jobcmd: /path/to/run_model.sh
           manual: Run the forecast model

This example defines a suite ``forecast`` containing a family ``prep`` with task ``get_obs``, and a top-level task ``run_model``.

Node Attributes
^^^^^^^^^^^^^^^

The following attributes may appear under any suite, family, or task node:

``vars:`` -- A mapping of variable name/value pairs to set as ecFlow edit variables on the node. For example:

.. code-block:: yaml

   task_run_model:
     vars:
       MEMBER: "001"
     script:
       ...

``trigger:`` -- A string expression defining the conditions under which a node may run. Only one ``trigger:`` is allowed per node. For example:

.. code-block:: yaml

   task_run_model:
     trigger: /forecast/prep/get_obs == complete
     script:
       ...

``defstatus:`` -- Sets the default status of a node. Accepted values are ``complete``, ``suspended``, ``aborted``, ``queued``, ``submitted``, ``active``, and ``unknown``. For example:

.. code-block:: yaml

   task_get_obs:
     defstatus: complete
     script:
       ...

``events:`` -- A list of named events attached to a node. Each item may be a string (event name) or a two-element list ``[number, name]``. For example:

.. code-block:: yaml

   task_get_obs:
     events:
       - obs_ready
       - [2, model_ready]
     script:
       ...

``limits:`` -- A list of limits defined on a suite or family. Each item is a two-element list ``[name, max_count]``. For example:

.. code-block:: yaml

   suite_forecast:
     limits:
       - [max_jobs, 4]

``inlimits:`` -- A list of limits that a node consumes. Each item may be a one-, two-, or three-element list ``[limit_name]``, ``[limit_path, limit_name]``, or ``[limit_path, limit_name, tokens]``. For example:

.. code-block:: yaml

   task_run_model:
     inlimits:
       - [/forecast, max_jobs]
     script:
       ...

``labels:`` -- A list of label name/value pairs on a node. Each item is a two-element list ``[name, value]``. For example:

.. code-block:: yaml

   task_run_model:
     labels:
       - [progress, "0%"]
     script:
       ...

``late:`` -- Defines late notification thresholds for a node. Accepts ``submitted``, ``active``, and ``complete`` as keys, each with a time value. For example:

.. code-block:: yaml

   task_run_model:
     late:
       submitted: "00:05:00"
       active: "02:00:00"
     script:
       ...

``meters:`` -- A list of meters on a node. Each item is a three- or four-element list ``[name, min, max]`` or ``[name, min, max, threshold]``. For example:

.. code-block:: yaml

   task_run_model:
     meters:
       - [progress, 0, 100]
     script:
       ...

Repeat Attributes
^^^^^^^^^^^^^^^^^

Only one ``repeat_*:`` attribute is allowed per node. The available repeat types are:

``repeat_date:`` -- Repeats over a date range. Requires ``variable``, ``start``, and ``end`` (as YYYYMMDD integers). Optional ``step`` (default 1).

.. code-block:: yaml

   suite_forecast:
     repeat_date:
       variable: YMD
       start: 20240101
       end: 20240131
       step: 1

``repeat_datelist:`` -- Repeats over an explicit list of dates (as YYYYMMDD integers). Requires ``variable`` and ``list``.

``repeat_datetime:`` -- Repeats over a datetime range. Requires ``variable``, ``start``, and ``end`` (as ``YYYYMMDDTHHmmss`` strings). Optional ``step`` (as ``HH:mm:ss``).

``repeat_day:`` -- Repeats by day increment. Requires ``step``.

``repeat_enumerated:`` -- Repeats over an explicit list of strings. Requires ``variable`` and ``list``.

``repeat_int:`` -- Repeats over an integer range. Requires ``variable``, ``start``, and ``end``. Optional ``step``.

``repeat_string:`` -- Repeats over an explicit list of strings. Requires ``variable`` and ``list``.

Task Script Block
-----------------

Tasks are required to have a ``script:`` block that defines the ecf script to generate. The ``script:`` block has the following keys:

``execution:`` -- **Required.** Defines the execution command for the task. See :doc:`/sections/user_guide/yaml/components/execution` documentation for full details. The ``executable:`` key is required by the schema. The ``jobcmd:`` key specifies the command to run inside the ecf script body, and is required by the code.

.. code-block:: yaml

   script:
     execution:
       executable: /path/to/run_model.sh
       jobcmd: /path/to/run_model.sh

``manual:`` -- Optional. A brief description of the task's purpose, embedded in the ecf script's ``%manual`` section. Defaults to ``"Script to run <taskname>"``.

``account:`` -- Optional. The account or project charged for batch jobs. Used when ``scheduler:`` is set at the workflow level.

``rundir:`` -- Optional. The directory in which the task will run. Used when ``scheduler:`` is set at the workflow level.

``pre_includes:`` -- Optional. A list of ecFlow include file names (without path) to include at the top of the generated ecf script, using ``%include <name>``.

``post_includes:`` -- Optional. A list of ecFlow include file names (without path) to include at the bottom of the generated ecf script.

.. code-block:: yaml

   task_run_model:
     script:
       account: myproject
       rundir: /path/to/run
       pre_includes:
         - head.h
       post_includes:
         - tail.h
       execution:
         executable: /path/to/run_model.sh
         jobcmd: /path/to/run_model.sh
         batchargs:
           walltime: "01:00:00"
       manual: Run the forecast model

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
             jobcmd: /path/to/run.sh
           manual: Run ensemble member {{ ec.MEM }}

This expands to three tasks named ``member_01``, ``member_02``, and ``member_03``.

Multiple expand variables of the same length may be provided together:

.. code-block:: yaml

   tasks_member_{{ ec.MEM }}_{{ ec.LABEL }}:
     expand:
       MEM: ["01", "02"]
       LABEL: ["ctrl", "pert"]

Generated Artifacts
-------------------

``suite.def`` -- The ecFlow suite definition file, written to ``<output-path>/suite.def``. If no ``--output-path`` is given, the suite definition is written to ``stdout``.

``*.ecf`` scripts -- One ecf script per task, written under ``<scripts-path>/``. Each script is nested under the ``<scripts-path>`` in the same manner as it is in the suite definition. The example above will output a script at ``<scripts-path>/forecast/prep/get_obs.ecf`` and at ``<scripts-path>/forecast/run_model``, where the script name is derived from the portion of the task name after the first underscore. Scripts are only generated when ``--scripts-path`` is provided to ``uw ecflow realize``.
