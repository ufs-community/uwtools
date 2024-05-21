``rocoto``
==========

The ``uw`` mode for realizing and validating Rocoto XML documents.

.. literalinclude:: rocoto/help.cmd
   :language: text
   :emphasize-lines: 1
.. literalinclude:: rocoto/help.out
   :language: text

.. _cli_rocoto_realize_examples:

``realize``
-----------

In ``uw`` terminology, to ``realize`` a configuration file is to transform it from its raw form into its final, usable state. In the case of ``uw rocoto``, that means transforming a structured UW YAML file into a :rocoto:`Rocoto XML<>` file. The structured YAML language required by UW closely follows the XML language defined by Rocoto.

More information about the structured UW YAML file for Rocoto can be found :any:`here<defining_a_workflow>`.

.. literalinclude:: rocoto/realize-help.cmd
   :language: text
   :emphasize-lines: 1
.. literalinclude:: rocoto/realize-help.out
   :language: text

Examples
^^^^^^^^

The examples in this section use a UW YAML file called ``rocoto.yaml`` with the following contents:

.. literalinclude:: rocoto/rocoto.yaml
   :language: yaml

* To realize a UW YAML input file to ``stdout`` in Rocoto XML format:

  .. literalinclude:: rocoto/realize-exec-stdout.cmd
     :language: text
     :emphasize-lines: 1
  .. literalinclude:: rocoto/realize-exec-stdout.out
     :language: xml

* To realize a UW YAML input file to a file named ``rocoto.xml``:

  .. literalinclude:: rocoto/realize-exec-file.cmd
     :language: text
     :emphasize-lines: 1
  .. literalinclude:: rocoto/realize-exec-file.out
     :language: text

  The content of ``rocoto.xml``:

  .. literalinclude:: rocoto/rocoto.xml
     :language: xml

* To read the UW YAML from ``stdin`` and write the XML to ``stdout``:

  .. literalinclude:: rocoto/realize-exec-stdin-stdout.cmd
     :language: text
     :emphasize-lines: 1
  .. literalinclude:: rocoto/realize-exec-stdin-stdout.out
     :language: xml

* To realize a UW YAML input file to a file named ``rocoto.xml`` in quiet mode:

  .. literalinclude:: rocoto/realize-exec-stdout-quiet.cmd
     :language: text
     :emphasize-lines: 1
  .. literalinclude:: rocoto/realize-exec-stdout-quiet.out
     :language: xml

  The contents of ``rocoto.xml`` are unchanged from the previous example.

* To realize a UW YAML file to a file named ``rocoto.xml`` with verbose log output (some output elided for brevity):

  .. literalinclude:: rocoto/realize-exec-stdout-verbose.cmd
     :language: text
     :emphasize-lines: 1
  .. literalinclude:: rocoto/realize-exec-stdout-verbose.out
     :language: xml

.. _cli_rocoto_validate_examples:

``validate``
------------

.. code-block:: text

   $ uw rocoto validate --help
   usage: uw rocoto validate [-h] [--version] [--input-file PATH] [--quiet] [--verbose]

   Validate Rocoto XML

   Optional arguments:
     -h, --help
         Show help and exit
     --version
         Show version info and exit
     --input-file PATH, -i PATH
         Path to input file (defaults to stdin)
     --quiet, -q
         Print no logging messages
     --verbose, -v
         Print all logging messages

Examples
^^^^^^^^

The examples in this section use a Rocoto XML file called ``rocoto.xml`` with the following content:

.. code-block:: xml
   :linenos:

   <?xml version='1.0' encoding='utf-8'?>
   <!DOCTYPE workflow [
     <!ENTITY ACCOUNT "myaccount">
     <!ENTITY FOO "test.log">
   ]>
   <workflow realtime="False" scheduler="slurm">
     <cycledef group="howdy">202209290000 202209300000 06:00:00</cycledef>
     <log>/some/path/to/&FOO;</log>
     <task name="hello" cycledefs="howdy">
       <account>&ACCOUNT;</account>
       <nodes>1:ppn=1</nodes>
       <walltime>00:01:00</walltime>
       <command>echo hello $person</command>
       <jobname>hello</jobname>
       <envar>
         <name>person</name>
         <value>siri</value>
       </envar>
     </task>
   </workflow>

* To validate an XML from ``stdin``:

  .. code-block:: text

     $ cat rocoto.xml | uw rocoto validate
     [2024-01-02T14:18:46]     INFO 0 Rocoto validation errors found

* To validate an XML from file ``rocoto.xml``:

  .. code-block:: text

     $ uw rocoto validate --input-file rocoto.xml
     [2024-01-02T14:18:46]     INFO 0 Rocoto validation errors found

* When the XML is invalid:

  In this example, the ``<command>`` line was removed from the XML.

  .. code-block:: text

     $ uw rocoto validate --input-file rocoto.xml
     [2024-01-10T21:54:51]    ERROR 3 Rocoto validation errors found
     [2024-01-10T21:54:51]    ERROR <string>:9:0:ERROR:RELAXNGV:RELAXNG_ERR_NOELEM: Expecting an element command, got nothing
     [2024-01-10T21:54:51]    ERROR <string>:9:0:ERROR:RELAXNGV:RELAXNG_ERR_INTERSEQ: Invalid sequence in interleave
     [2024-01-10T21:54:51]    ERROR <string>:9:0:ERROR:RELAXNGV:RELAXNG_ERR_CONTENTVALID: Element task failed to validate content
     [2024-01-10T21:54:51]    ERROR Invalid Rocoto XML:
     [2024-01-10T21:54:51]    ERROR  1 <?xml version='1.0' encoding='utf-8'?>
     [2024-01-10T21:54:51]    ERROR  2 <!DOCTYPE workflow [
     [2024-01-10T21:54:51]    ERROR  3   <!ENTITY ACCOUNT "myaccount">
     [2024-01-10T21:54:51]    ERROR  4   <!ENTITY FOO "test.log">
     [2024-01-10T21:54:51]    ERROR  5 ]>
     [2024-01-10T21:54:51]    ERROR  6 <workflow realtime="False" scheduler="slurm">
     [2024-01-10T21:54:51]    ERROR  7   <cycledef group="howdy">202209290000 202209300000 06:00:00</cycledef>
     [2024-01-10T21:54:51]    ERROR  8   <log>/some/path/to/&FOO;</log>
     [2024-01-10T21:54:51]    ERROR  9   <task name="hello" cycledefs="howdy">
     [2024-01-10T21:54:51]    ERROR 10     <account>&ACCOUNT;</account>
     [2024-01-10T21:54:51]    ERROR 11     <nodes>1:ppn=1</nodes>
     [2024-01-10T21:54:51]    ERROR 12     <walltime>00:01:00</walltime>
     [2024-01-10T21:54:51]    ERROR 13     <jobname>hello</jobname>
     [2024-01-10T21:54:51]    ERROR 14     <envar>
     [2024-01-10T21:54:51]    ERROR 15       <name>person</name>
     [2024-01-10T21:54:51]    ERROR 16       <value>siri</value>
     [2024-01-10T21:54:51]    ERROR 17     </envar>
     [2024-01-10T21:54:51]    ERROR 18   </task>
     [2024-01-10T21:54:51]    ERROR 19 </workflow>

  To decode this type of output, it is easiest to interpret it from the bottom up. It says:

  * The task starting at Line 9 has invalid content.
  * There was an invalid sequence.
  * It was expecting a ``<command>`` element, but there wasn't one.

  In the following example, an empty ``<dependency>`` element was added at the end of the task:

  .. code-block:: xml
     :linenos:

     <?xml version='1.0' encoding='utf-8'?>
     <!DOCTYPE workflow [
       <!ENTITY ACCOUNT "myaccount">
       <!ENTITY FOO "test.log">
     ]>
     <workflow realtime="False" scheduler="slurm">
       <cycledef group="howdy">202209290000 202209300000 06:00:00</cycledef>
       <log>/some/path/to/&FOO;</log>
       <task name="hello" cycledefs="howdy">
         <account>&ACCOUNT;</account>
         <nodes>1:ppn=1</nodes>
         <walltime>00:01:00</walltime>
         <command>echo hello $person</command>
         <jobname>hello</jobname>
         <envar>
           <name>person</name>
           <value>siri</value>
         </envar>
         <dependency>
         </dependency>
       </task>
     </workflow>

  .. code-block:: text

     $ uw rocoto validate --input-file rocoto.xml
     [2024-01-10T21:56:14]    ERROR 2 Rocoto validation errors found
     [2024-01-10T21:56:14]    ERROR <string>:0:0:ERROR:RELAXNGV:RELAXNG_ERR_INTEREXTRA: Extra element dependency in interleave
     [2024-01-10T21:56:14]    ERROR <string>:9:0:ERROR:RELAXNGV:RELAXNG_ERR_CONTENTVALID: Element task failed to validate content
     [2024-01-10T21:56:14]    ERROR Invalid Rocoto XML:
     [2024-01-10T21:56:14]    ERROR  1 <?xml version='1.0' encoding='utf-8'?>
     [2024-01-10T21:56:14]    ERROR  2 <!DOCTYPE workflow [
     [2024-01-10T21:56:14]    ERROR  3   <!ENTITY ACCOUNT "myaccount">
     [2024-01-10T21:56:14]    ERROR  4   <!ENTITY FOO "test.log">
     [2024-01-10T21:56:14]    ERROR  5 ]>
     [2024-01-10T21:56:14]    ERROR  6 <workflow realtime="False" scheduler="slurm">
     [2024-01-10T21:56:14]    ERROR  7   <cycledef group="howdy">202209290000 202209300000 06:00:00</cycledef>
     [2024-01-10T21:56:14]    ERROR  8   <log>/some/path/to/&FOO;</log>
     [2024-01-10T21:56:14]    ERROR  9   <task name="hello" cycledefs="howdy">
     [2024-01-10T21:56:14]    ERROR 10     <account>&ACCOUNT;</account>
     [2024-01-10T21:56:14]    ERROR 11     <nodes>1:ppn=1</nodes>
     [2024-01-10T21:56:14]    ERROR 12     <walltime>00:01:00</walltime>
     [2024-01-10T21:56:14]    ERROR 13     <command>echo hello $person</command>
     [2024-01-10T21:56:14]    ERROR 14     <jobname>hello</jobname>
     [2024-01-10T21:56:14]    ERROR 15     <envar>
     [2024-01-10T21:56:14]    ERROR 16       <name>person</name>
     [2024-01-10T21:56:14]    ERROR 17       <value>siri</value>
     [2024-01-10T21:56:14]    ERROR 18     </envar>
     [2024-01-10T21:56:14]    ERROR 19     <dependency>
     [2024-01-10T21:56:14]    ERROR 20     </dependency>
     [2024-01-10T21:56:14]    ERROR 21   </task>
     [2024-01-10T21:56:14]    ERROR 22 </workflow>

  Once again, interpreting from the bottom:

  * The content of the task starting at Line 9 is not valid.
  * There is an extra element ``<dependency>`` in the task.
