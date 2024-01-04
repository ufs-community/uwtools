
Defining a Rocoto Workflow
==========================

:rocoto:`Rocoto<>` is a workflow manager widely used by :ufs:`UFS<>` users and developers. It uses a custom XML language to define a set of tasks, their computatioal resource needs on a batch system, and their dependencies. 

To date, it has been challenging to manage XML files that must support a multitude of workflow options. The ``uw rocoto`` tool defines a YAML language that can be easily manipulated like any other key/value configuration file and translates it into the syntax required by Rocoto. This enables flexibility to arbitrarily make changes to any workflow while UFS Apps can track the highest priority configurations for Commumity and Operational use.


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

YAML Entries
............

``attrs``: This section allows users to define any number of the available attributes available to the workflow tag in Rocoto's native XML language. Set them with a key/value that matches the exact syntax needed by Rocoto. These attributes work to fill in the ``<workflow>`` tag. For example,

.. code:: XML

  <workflow realtime="false" scheduler="slurm">
  ...
  </workflow>

``cycledef``: This section is comprised of a list of grouped cycle definitions for a workflow. Any number of entries is supported. Similar to ``attrs`` for the ``workflow`` level, this entry, too has an ``attrs`` tag that follows the exact requirements of those in the Rocoto XML language. The ``spec`` entry is required and supports either the "start, stop, step" syntax, or the "crontab-like" method supported by Rocoto. The example above translates to a single cycledef:

.. code:: XML

  <cycledef group="howdy">202209290000 202209300000 06:00:00</cycledef>

``entities``: This section is a set of key/value pairs where the keys are the named entities (or XML variables) and the values track to the values of those XML entities. Each entry shows up as an entry like ``<!ENTITY key "value">``. The example above would yield:

.. code:: XML

  <?xml version='1.0' encoding='utf-8'?>
  <!DOCTYPE workflow [
    <!ENTITY ACCOUNT "myaccount">
    <!ENTITY FOO "test.log">
  ]>

``log``: This is a path-like string that defines where to put the Rocoto logs. It corresponds to the ``<log>`` tag. For example:

.. code:: XML

  <log>/some/path/to/&FOO;</log>


``tasks``: This section will be explained in detail in the next section.


Using Cycle Strings
...................

The ``<cyclestr>`` tag in Rocoto transforms specific flags to represent components of the current cycle at run time. For example, an ISO date string like ``2023-01-01T12:00:00`` is represented as ``'@Y-@m-@dT@X'``. See the :rocoto:`Rocoto documentation<>` for full details. In the Rocoto YAML, the ``cyclestr:`` entry can be used anywhere that Rocoto will accept a ``<cyclestr>`` to acheive this result. The required structure of a ``cyclestr:`` entry is a ``value:``, like this:

.. code::

  entities:
    FOO: test@Y-@m-@dT@X.log
  log:
    cyclestr:
      value: /some/path/to/&FOO;

In the example, the resulting log would appear in the XML file as:

.. code:: XML

  <log>
    <cyclestr>/some/path/to/&FOO;</cyclestr>
  </log>

The ``attrs:`` section is optional within the ``cyclestr:`` entry, and can be used to specifiy the cycle offset.

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
    nodes: 1:ppn=1
    walltime: 00:01:00
    envars:
      person: siri
    dependencies:

Each task is named by its YAML entry. Entries under ``tasks`` prefixed with ``task_`` will be named with what follows the prefix. In the example above the task will be named ``hello`` and will appear in the XML like this:

.. code:: XML

  <task name="hello" cycledefs="howdy">
    <jobname>hello</jobname>
    ...
  </task>

where the ``attrs`` section may set any of the Rocoto-allowed XML attributes. The ``<jobname>`` tag will use the same name. 

The name of the task can be any string accepted by Rocoto as a task name (including additional underscores), but must contain the leading ``task_`` to be recognized as a task.

``command``: The command that will be run in the batch job.

``envars``: Any number of key/value pairs to set up the environment for the ``<command>`` to run successfully. Here, keys translate to bash variable names and values translate to the bash variables' values. Each entry in this section will show up in the XML like this:

.. code:: XML

  <envar>
    <name>person</name>
    <value>siri</value>
  </envar>

``dependencies``: [Optional] Any number of dependencies accepted by Rocoto. This entry is described in more detail below.


The other tags not specifically mentioned here are follow the same conventions as described in the :rocoto:`Rocoto<>` documentation.



Defining Dependencies for Tasks
...............................

Rocoto dependencies are optional entries that are structured as boolean expressions defining the readiness of a task to be submitted to the queue. The :rocoto:`Rocoto documentation<>` explains each tag in detail. Here is an explanation for how those tags should be specified in YAML format.

There are many similarities, but some nuanced differences must be clarified.

Each dependency represented in the YAML will be named exactly the same as a dependency in Rocoto XML, but can be suffixed with an arbitary descriptor for the dependency after an underscore (``_``). For example, a ``<streq>`` tag could be in the YAML under ``streq_check_flag:`` or similar. Additional underscores are allowed.

Tag Attributes
______________

Each of the dependiences that require XML attributes (the "key=value" parts inside the XML tag) can be specified with an ``attrs`` entry. For example:

.. code::

  task_hello:
    command: "hello world"
    ...
  task_goodbye:
    command: "goodbye"
    dependencies:
       taskdep:
         attrs:
           task: hello

Here, the Rocoto ``taskdep`` says that the ``goodbye`` task cannot be submitted until the ``hello`` task is complete. This will result in Rocoto XML that looks like the following snippet:

.. code:: XML

  <task name="hello">
    ...
  </task>
  <task name="goodbye"/>
    ...
    <dependency>
      <taskdep task="hello"/>
    </dependency>
  </task>

Repeated Dependencies and Boolean Operators
___________________________________________

Because YAML represents a hash table (a dictionary in Python), each entry at the same level must be unique. To accomplish this in the YAML format, any of the dependencies may be specified with an arbitrary unique suffix following an underscore (``_``). We recommend a descriptive one to make it easier to read. In the following example, there are multiple data dependencies for the basic ``hello`` task.

.. code::

  task_hello:
    command: "hello world"
    ...
    dependencies:
      and:
        datadep_foo:
          value: "foo.txt"
        datadep_bar:
          value: "bar.txt"


This would result in Rocoto XML in this form:

.. code:: XML

  <task name="hello"/>
    ...
    <dependency>
      <and>
        <datadep>"foo.txt"</datadep>
        <datadep>"bar.txt"</datadep>
      </and>
    </dependency>
  </task>

The ``datadep_foo:`` and ``datadep_bar:`` YAML entries were named arbitrarily after the first ``_``, but could have been even more descriptive such as ``datadep_foo_file:`` or ``datadep_foo_text:``. The important part is that the leading tag match that in Rocoto.

This example also demonstrates the use of Rocoto's **boolean operator tags** in the structured YAML, e.g. ``<or>``, ``<not>``, etc.. The structure follows the tree in the Rocoto XML language in that each of the sub-elements of the ``<and>`` tag translate to sub-entries in YAML. Multiple of the boolean operator tags can be set at the same level just as with any other tag type by adding a discriptive suffix starting with an underscore (``_``). In the above example, the ``and:`` entry could have equivalently been named ``and_data_files:`` to achieve an identical Rocoto XML result.


Defining Metatasks
..................

A Rocoto ``metatask`` is a structure that allows for the single specification of a task or group of tasks to run with parameterized input. The ``metatask`` requires the definition of at least one parameter variable, but multiple may be specified, in which case there must be the same number of entries for all parameter variables. To achieve a combination of variables, nested metatasks would be necessary. Here is an example of the YAML specification for running our "hello world" example in a variety of languages:

.. code:: text

  metatask_greetings:
    var:
      greeting: hello hola bonjour
      person: Jane John Jenn
    task_#greeting#:
      command: "echo #greeting# #world#"
      ...

This translates to Rocoto XML (whitespace added for readability):

.. code:: XML

  <metatask name=greetings/>

    <var name="greeting">hello hola bonjour</var>
    <var name="person">Jane John Jenn</var>

    <task name='#greeting#'>

      <command>echo #greeting# #person#<command>
      ...

    </task>
  </metatask>


YAML Definitions
~~~~~~~~~~~~~~~~


The ``<cyclestr>`` tag
......................

.. code::

  cyclestr:
    value: "/some/path/to/workflow_@Y@m@d@H.log"      # required
    attrs:
      offset: "1:00:00"

.. code::

  <cyclestr offset="1:00:00">"/some/path/to/workflow_@Y@m@d@H.log"</cyclestr>

The ``<workflow>`` tags
.......................

.. code::

  workflow:
    attrs:
      cyclethrottle: 2
      realtime: true     # required
      scheduler: slurm   # required
      taskthrottle: 20

.. code:: XML

  <workflow cyclethrottle="2" realtime="true" scheduler="slurm" taskthrottle="20">
    ...
  <workflow>

Defining Cycles
_________________

At least one ``cycledef:`` is required.

.. code::

  cycledef:
    - attrs:
        group: synop
        activation_offset: "-1:00:00"
      spec: 202301011200 202301021200 06:00:00    # Also accepts crontab-like string
    - attrs:
        group: hourly
      spec: 202301011200 202301021200 01:00:00    # Also accepts crontab-like string

.. code:: XML

  <cycledef group="synop" activation_offset="-1:00:00">202301011200 202301021200 06:00:00</cycledef>
  <cycledef group="hourly">202301011200 202301021200 01:00:00</cycledef>

Defining Entities
_________________

Enties are optional. Any number of entities may be specified.

.. code::

  entities:
    FOO: 12
    BAR: baz

.. code:: XML

  <?xml version="1.0"?>
  <!DOCTYPE workflow
  [
      <!ENTITY FOO "12">
      <!ENTITY BAR "baz">
  ]>

Defining the worklfow log
_________________________

``log:`` is a required entry.


.. code::

  log: /some/path/to/workflow.log

.. code:: XML

  <log>/some/path/to/workflow.log</log>

or

.. code::

  log:
    cyclestr:
      value: /some/path/to/workflow_@Y@m@d.log

.. code:: XML

  <log><cyclestr>/some/path/to/workflow_@Y@m@d.log</cyclestr></log>


Defining the set of tasks
_________________________

At least one task or metatask must be defined in the task section.

.. code::

  tasks:
    task_*:
    metatask_*


The ``<task>`` tag
..................


.. code::

  task_foo:
    attrs:
      cycledefs: hourly
      maxtries: 2
      throttle: 10
      final: false
    command: echo hello world
    walltime: 00:10:00
    cores: 1


.. code::

  <task name="foo" cycledefs:"hourly" maxtries="2" throttle="10" final="False">
    ...
  </task>


The following entries take strings just like in the ``command`` example above. Please see the :rocoto:`Rocoto documentation<>` for specifics on how to set them.

.. code::

  account:
  exclusive:
  jobname:
  join:
  memory:
  native:
  nodes:
  partition:
  queue:
  rewind:
  shared:
  stderr:
  stdout:

The following YAML entries need values that can be integers, strings, or ``cyclestr:`` entries.

.. code::

  command:
  deadline:
  jobname:
  join:
  native:
  stderr:
  stdout:


