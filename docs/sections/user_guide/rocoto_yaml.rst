.. _defining_a_workflow:

Defining a Rocoto Workflow
==========================

:rocoto:`Rocoto<>` is a workflow manager widely used by :ufs:`UFS<>` users and developers. It uses a custom XML language to define a set of tasks, their computational resource needs on a batch system, and their dependencies. 

To date, it has been challenging to manage XML files that must support a multitude of workflow options. The ``uw rocoto`` tool defines a UW YAML language that can be easily manipulated like any other key/value configuration file and translates it into the syntax required by Rocoto. This enables flexibility to arbitrarily make changes to any workflow while UFS Apps can track the highest priority configurations for Community and Operational use.


Workflow Section
~~~~~~~~~~~~~~~~
Starting at the top level of the UW YAML config for Rocoto, there are several required sections. See the example and explanation below:

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

UW YAML Entries
...............

``attrs:``: This section allows users to define any number of the available attributes to the ``<workflow>`` tag in Rocoto's native XML language. Set each with a key/value that matches the exact syntax needed by Rocoto. These attributes work to fill in the ``<workflow>`` tag. For example,

.. code:: XML

  <workflow realtime="false" scheduler="slurm">
  ...
  </workflow>

``cycledef:``: This section is a list of grouped cycle definitions for a workflow. Any number of entries is supported. Similar to ``attrs:`` for the ``workflow:`` level, this entry has an ``attrs:`` tag that follows the exact requirements of those in the Rocoto XML language. The ``spec:`` entry is required and supports either the "start, stop, step" syntax, or the "crontab-like" method supported by Rocoto. The example above translates to a single ``<cycledef>`` tag:

.. code:: XML

  <cycledef group="howdy">202209290000 202209300000 06:00:00</cycledef>

``entities:``: This section defines key/value pairs -- each rendered as ``<!ENTITY key "value">`` -- to translate to named entities (variables) in XML. The example above would yield:

.. code:: XML

  <?xml version='1.0' encoding='utf-8'?>
  <!DOCTYPE workflow [
    <!ENTITY ACCOUNT "myaccount">
    <!ENTITY FOO "test.log">
  ]>

``log:``: This is a path-like string that defines where to put the Rocoto logs. It corresponds to the ``<log>`` tag. For example:

.. code:: XML

  <log>/some/path/to/&FOO;</log>


``tasks:``: This section is explained in the ``Tasks Section``.


Using Cycle Strings
...................

The ``<cyclestr>`` tag in Rocoto transforms specific flags to represent components of the current cycle at run time. For example, an ISO date string like ``2023-01-01T12:00:00`` is represented as ``'@Y-@m-@dT@X'``. See the :rocoto:`Rocoto documentation<>` for full details. In the UW YAML, the ``cyclestr:`` entry can be used anywhere that Rocoto will accept a ``<cyclestr>`` to achieve this result. The required structure of a ``cyclestr:`` entry is a ``value:``, like this:

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

The ``attrs:`` section is optional within the ``cyclestr:`` entry, and can be used to specify the cycle offset.

Tasks Section
~~~~~~~~~~~~~

The ``tasks:`` section is a nested structure that can be arbitrarily deep and defines all the tasks and metatasks in a Rocoto workflow. One or more task or metatask entries are required in this high-level ``tasks:`` section.

Defining Tasks
..............

Let's dissect the following task example:

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

Each task is named by its UW YAML entry. Entries under ``tasks:`` prefixed with ``task_`` will be named with what follows the prefix. In the example above the task will be named ``hello`` and will appear in the XML like this:

.. code:: XML

  <task name="hello" cycledefs="howdy">
    <jobname>hello</jobname>
    ...
  </task>

where the ``attrs:`` section may set any of the Rocoto-allowed XML attributes. The ``<jobname>`` tag will, by default, use the same name, but may be overridden with an explicit ``jobname:`` entry under the task.

The name of the task can be any string accepted by Rocoto as a task name (including additional underscores), but must contain the leading ``task_`` to be recognized as a task.

``command:``: The command that will be run in the batch job.

``envars:``: Any number of key/value pairs defining bash variable names and their corresponding values, to be exported to the environment in which ``<command>`` will run, each rendered in XML like this:

.. code:: XML

  <envar>
    <name>person</name>
    <value>siri</value>
  </envar>

``dependencies:``: [Optional] Any number of dependencies accepted by Rocoto. This entry is described in more detail below.


The other tags not specifically mentioned here follow the same conventions as described in the :rocoto:`Rocoto<>` documentation.



Defining Dependencies for Tasks
...............................

Optional dependencies, structured as boolean expressions, define the readiness of a task to run. Dependency specification in YAML is described here; see the :rocoto:`Rocoto documentation<>` for more details.

UW YAML dependency key names should mirror Rocoto XML dependency tag names, optionally suffixed with an underscore followed by an arbitrary descriptor. For example, a ``<streq>`` tag might appear in YAML as ``streq_check_flag:``.

Tag Attributes
______________

Each of the dependencies that require attributes (the ``key="value"`` parts inside the XML tag) can be specified with an ``attrs:`` entry. For example:

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

Here, the ``taskdep:`` dependency says that the ``goodbye`` task cannot run until the ``hello`` task is complete. The resulting Rocoto XML looks like this:

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

Because UW YAML represents a hash table (a dictionary in Python), each entry at the same level must be unique. To accomplish this in the UW YAML format, any of the dependencies can be specified with an arbitrary unique suffix following an underscore. When duplicates appear at the same level, they *must* have unique names. In the following example, there are multiple data dependencies for the basic ``hello`` task.

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

The ``datadep_foo:`` and ``datadep_bar:`` UW YAML entries were named arbitrarily after the first ``_``, but could have been even more descriptive such as ``datadep_foo_file:`` or ``datadep_foo_text:``. The important part is that the YAML key prefix matches the Rocoto XML tag name.

This example also demonstrates the use of Rocoto's **boolean operator tags** in the structured UW YAML, e.g. ``<or>``, ``<not>``, etc.. The structure follows the tree in the Rocoto XML language in that each of the sub-elements of the ``<and>`` tag translate to sub-entries in UW YAML. Multiple of the boolean operator tags can be set at the same level just as with any other tag type by adding a descriptive suffix starting with an underscore (``_``). In the above example, the ``and:`` entry could have equivalently been named ``and_data_files:`` to achieve an identical Rocoto XML result.


Defining Metatasks
..................

A Rocoto ``metatask`` expands into one or more tasks via substitution of values, defined under the ``var:`` key, into placeholders bracketed with ``#``s. Each variable must provide the same number of values. Here is UW YAML that localizes a greeting to a variety of languages:

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


UW YAML Definitions
~~~~~~~~~~~~~~~~~~~


In this section, the example in UW YAML will be followed by its representation in Rocoto XML.


The ``<cyclestr>`` tag
......................

.. code::

  cyclestr:
    value: "/some/path/to/workflow_@Y@m@d@H.log" # required
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

Entities are optional. Any number of entities may be specified.

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

Defining the workflow log
_________________________

``log:`` is a required entry.


.. code::

  log: /some/path/to/workflow.log

.. code:: XML

  <log>/some/path/to/workflow.log</log>

A cycle string may be specified here, instead.

.. code::

  log:
    cyclestr:
      value: /some/path/to/workflow_@Y@m@d.log

.. code:: XML

  <log><cyclestr>/some/path/to/workflow_@Y@m@d.log</cyclestr></log>


Defining the set of tasks
_________________________

At least one task or metatask must be defined in the ``tasks:`` section.

.. code::

  tasks:
    task_*:
    metatask_*


The ``<task>`` tag
..................

Multiple ``task_*:`` YAML entries may exist under the ``dependency:`` entry, or any of the
``metatask_*:`` entries. At least one must be specified per workflow.

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


The following entries take strings just like in the ``command:`` example above. Please see the :rocoto:`Rocoto documentation<>` for specifics on how to set them.

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

The following UW YAML entries require values that are integers, strings, or ``cyclestr:`` entries.

.. code::

  command:
  deadline:
  jobname:
  join:
  native:
  stderr:
  stdout:

The ``<dependency>`` tag
........................

The ``<dependency>`` tag has many different tags for defining the readiness of a task to run. They may be categorized in several ways: boolean operator tags, comparison tags, and dependencies.

Boolean Operator Tags
_____________________

All of the boolean operator tags require **one or more additional dependency tags** from any category in the sub-tree of the entry.

.. code:: text

  and:
  or:
  not:
  nand:
  nor:
  xor:
  some:

Comparison Tags
_______________

Both the ``streq:`` and ``strneq:`` UW YAML entries are specified the same way. The sub-tree ``left:`` and ``right:`` entries both accept a ``cyclestr:`` if needed.

.. code::

  streq:
    left: &FOO;
    right: bar

.. code:: XML

  <dependency>
    <streq>
      <left>&FOO;</left>
      <right>bar</right>
    </streq>
  </dependency>

Dependency tags
_______________

These tags define dependencies on other tasks, metatasks, data, or wall time.

* The task dependency

.. code::

  taskdep:
    attrs:
      cycle_offset: "-06:00:00"
      state: succeeded
      task: hello                # required

.. code:: XML

  <dependency>
    <taskdep task="hello" state="succeeded" cycle_offset="-06:00:00"/>
  </dependency>


* The metatask dependency

.. code::

  metataskdep:
    attrs:
      cycle_offset: "-06:00:00"
      state: succeeded
      metatask: greetings            # required
      threshold: 1

.. code:: XML

  <dependency>
    <metataskdep metatask="greetings" state="succeeded" cycle_offset="-06:00:00" threshold="1"/>
  </dependency>


The ``value:`` entry for ``datadep:`` accepts a ``cyclestr:`` structure.

.. code::

  datadep:
    attrs:
      age: 120
      minsize: 1024b
    value: /path/to/a/file.txt     # required

.. code:: XML

  <dependency>
    <datadep age="120" minsize="1024b">/path/to/a/file.txt</datadep>
  </dependency>


The ``timedep:`` entry will almost certainly want a ``cyclestr:`` structure.

.. code:: text

  timedep:
    cyclestr:
      value: @Y@m@d@H@M@S

.. code:: XML

  <dependency>
    <timedep><cyclestr>@Y@m@d@H@M@S</cyclestr></timedep>
  </dependency>


The ``<metatask>`` tag
......................

One or more metatasks may be included under the ``dependency:`` entry, or nested under other
``metatask_*:`` entries.

Here is an example of specifying a nested metatask entry.

.. code:: text

  metatask_member:
    var:
      member: 001 002 003
    metatask_graphics_#member#_field:
      var:
        field: temp u v
      task_graphics_mem#member#_#field#:
        command: "echo $member $field"
        envars:
          member: #member#
          field: #field#
        ...


This will run tasks named:

.. code::

  graphics_mem001_temp
  graphics_mem002_temp
  graphics_mem003_temp
  graphics_mem001_u
  graphics_mem002_u
  graphics_mem003_u
  graphics_mem001_v
  graphics_mem002_v
  graphics_mem003_v

The XML will look like this

.. code:: XML

  <metatask name="member">
    <var name="member">001 002 003</var>

    <metatask name="graphics_#member#_field">
      <var name="field">001 002 003</var>

      <task name="graphics_mem#member#_#field#">
        <command>"echo $member $field"</command>
        <envar>
          <name>member</name>
          <value>mem#member#</value>
        </envar>
        <envar>
          <name>field</name>
          <value>#field#</value>
        </envar>
        ...
      </task>

    </metatask>
  </metatask>
