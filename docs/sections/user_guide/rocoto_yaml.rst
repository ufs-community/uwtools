
Defining a Rocoto Workflow
==========================

:rocoto:`Rocoto<>` is a workflow manager widely used by :ufs:`UFS<>` users and developers. It uses a custom XML language to define a set of tasks, their computatioal resource needs on a batch system, and their dependencies. 

To date, it has been challenging to manage XML files that must support a multitude of workflow options. The ``uw rocoto`` tool defines a YAML language that can be easily manipulated like any other key/value configuration file and translates it into the syntax required by Rocoto. This enables flexibility to arbitrarily make changes to any workflow while UFS Apps can track the highest priority configurations for Commumity and Operational use.


The Structured YAML
-------------------

Workflow Section
~~~~~~~~~~~~~~~~
Starting at the top level of the YAML config for Rocoto, there are several requried sections. See the example and explanation below:

  .. code::

    workflow:
      attrs:
        realtime: false
        scheduler: slurm
      cycledef:
        - attrs:
            activation_offset: -06:00
            group: howdy
          spec: 202209290000 202209300000 06:00:00
      entities:
        ACCOUNT: myaccount
        FOO: test.log
      log: /some/path/to/&FOO;
      tasks:
        ...


``attrs``: This section allows users to define any number of the available attributes available to the workflow tag in Rocoto's native XML language. Set them with a key/value that matches the exact syntax needed by Rocoto. These attributes work to fill in the ``<workflow>`` tag. For example,

  .. code::

    <workflow realtime="false" scheduler="slurm">
    ...
    </workflow>

``cycledef``: This section is comprised of a list of grouped cycle definitions for a workflow. Any number of entries is supported. Similar to ``attrs`` for the ``workflow`` level, this entry, too has an ``attrs`` tag that follows the exact requirements of those in the Rocoto XML language. The ``spec`` entry is required and supports either the "start, stop, step" syntax, or the "crontab-like" method supported by Rocoto. The example above translates to a single cycledef:

  .. code::

    <cycledef group="howdy">202209290000 202209300000 06:00:00</cycledef>

``entities``: This section is a set of key/value pairs where the keys are the named entities (or XML variables) and the values track to the values of those XML entities. Each entry shows up as an entry like ``<!ENTITY key "value">``. The example above would yield:

  .. code::

    <?xml version='1.0' encoding='utf-8'?>
    <!DOCTYPE workflow [
      <!ENTITY ACCOUNT "myaccount">
      <!ENTITY FOO "test.log">
    ]>

``log``: This is a path-like string that defines where to put the Rocoto logs. It corresponds to the ``<log>`` tag. For example:

  .. code::

    <log>/some/path/to/&FOO;</log>


``tasks``: This section will be explained in detail in the next section.


Tasks Section
~~~~~~~~~~~~~

The ``tasks`` section is a nested structure that can be arbitrarily deep and defines all the tasks and metatasks in a Rocoto workflow. One or more task or metatask entries is required in this high-level ``tasks`` section.

Defining Tasks
..............

Let's disect the following task example:

  .. code::

    task_hello:
      attrs:
        cycledefs: howdy
      account: "&ACCOUNT;"
      command: "echo hello $person"
      join: '&FOO;/{{ jobname }}.log'
      nodes: 1:ppn=1
      walltime: 00:01:00
      envars:
        person: siri
      dependencies:

Each task is named by its YAML entry. Entries under ``tasks`` prefixed with ``task_`` will be named with what follows the prefix. In the example above the task will be named ``hello`` and will appear in the XML like this:

  .. code::

    <task name="hello" cycledefs="howdy">
      <jobname>hello</jobname>
      <join>&FOO;/hello.log</join>

      ...
    </task>

where the ``attrs`` section may set any of the Rocoto-allowed XML attributes. The ``<jobname>`` tag will use the same name. Even though it does not appear in the input YAML, you may use ``jobname`` in your YAML Jinja2 entries for consistency in naming. For example, here the ``join`` tag names the log consistently with the task name and the job name.


``command``: The command that will be run in the batch job.

``envars``: Any number of key/value pairs to set up the environment for the ``<command>`` to run successfully. Here, keys translate to bash variable names and values translate to the bash variables' values. Each entry in this section will show up in the XML like this:

  .. code::

    <envar>
      <name>person</name>
      <value>siri</value>
    </envar>

``dependencies``: [Optional] Any number of dependencies accepted by Rocoto. This entry is described in more detail below.


The other tags not specifically mentioned here are follow the same conventions as described in the :rocoto:`Rocoto<>` documentation.


Defining Dependencies for Tasks
...............................




