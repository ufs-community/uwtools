.. important::

  **Task Naming Convention**: Task keys must follow the pattern ``task_<name>``. When ``ecf`` scripts are generated, the ``<name>`` portion becomes the script filename with a ``.ecf`` extension. See :ref:`ecflow_workflows` for more information about the structured UW YAML for ecFlow.

   Examples:

   - ``task_fetch`` → ``fetch.ecf``
   - ``task_run_model`` → ``model.ecf``
   - ``task_process_output_files`` → ``process_output_files.ecf``

   Names for suites and families follow a corresponding naming convention.
