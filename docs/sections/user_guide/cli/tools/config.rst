``config``
==========

The ``uw`` mode for handling configuration files (configs).

.. code-block:: text

   $ uw config --help
   usage: uw config [-h] [--version] ACTION ...

   Handle configs

   Optional arguments:
     -h, --help
         Show help and exit
     --version
         Show version info and exit

   Positional arguments:
     ACTION
       compare
         Compare configs
       realize
         Realize config
       validate
         Validate config

.. _cli_config_compare_examples:

``compare``
-----------

The ``compare`` action lets users compare two config files.

.. code-block:: text

   $ uw config compare --help
   usage: uw config compare --file-1-path PATH --file-2-path PATH [-h] [--version]
                            [--file-1-format {ini,nml,sh,yaml}] [--file-2-format {ini,nml,sh,yaml}]
                            [--quiet] [--verbose]

   Compare configs

   Required arguments:
     --file-1-path PATH
         Path to file 1
     --file-2-path PATH
         Path to file 2

   Optional arguments:
     -h, --help
         Show help and exit
     --version
         Show version info and exit
     --file-1-format {ini,nml,sh,yaml}
         Format of file 1
     --file-2-format {ini,nml,sh,yaml}
         Format of file 2
     --quiet, -q
         Print no logging messages
     --verbose, -v
         Print all logging messages

Examples
^^^^^^^^

The examples that follow use namelist files ``values1.nml`` and ``values2.nml``, both initially with the following contents:

.. code-block:: fortran

   &values
     greeting = "Hello"
     recipient = "World"
   /

* To compare two config files with the same contents:

  .. code-block:: text

     $ uw config compare --file-1-path values1.nml --file-2-path values2.nml
     [2024-01-08T16:53:04]     INFO - values1.nml
     [2024-01-08T16:53:04]     INFO + values2.nml
     [2024-01-08T16:53:04]     INFO ---------------------------------------------------------------------

* If there are differences between the config files, they will be shown below the dashed line. For example, with ``recipient: World`` removed from ``values1.nml``:

  .. code-block:: text

     $ uw config compare --file-1-path values1.nml --file-2-path values2.nml
     [2024-01-08T16:54:03]     INFO - values1.nml
     [2024-01-08T16:54:03]     INFO + values2.nml
     [2024-01-08T16:54:03]     INFO ---------------------------------------------------------------------
     [2024-01-08T16:54:03]     INFO values:       recipient:  - None + World

* If a config file has an unrecognized (or no) extension, ``uw`` will not know how to parse its contents:

  .. code-block:: text

     $ uw config compare --file-1-path values.txt --file-2-path values1.nml
     Cannot deduce format of 'values.txt' from unknown extension 'txt'

  In this case, the format can be explicitly specified (``values.txt`` is a copy of ``values1.nml``):

  .. code-block:: text

     $ uw config compare --file-1-path values.txt --file-1-format nml --file-2-path values2.nml
     [2024-01-08T16:56:54]     INFO - values.txt
     [2024-01-08T16:56:54]     INFO + values2.nml
     [2024-01-08T16:56:54]     INFO ---------------------------------------------------------------------
     [2024-01-08T16:56:54]     INFO values:       recipient:  - None + World

* To request verbose log output:

  .. code-block:: text

     $ uw config compare --file-1-path values1.nml --file-2-path values2.nml --verbose
     [2024-01-08T16:57:28]    DEBUG Command: uw config compare --file-1-path values1.nml --file-2-path values2.nml --verbose
     [2024-01-08T16:57:28]     INFO - values1.nml
     [2024-01-08T16:57:28]     INFO + values2.nml
     [2024-01-08T16:57:28]     INFO ---------------------------------------------------------------------
     [2024-01-08T16:57:28]     INFO values:       recipient:  - None + World

  If additional information is needed, ``--debug`` can be used which will return the stack trace from any unhandled exception as well.

  Note that ``uw`` logs to ``stderr``, so the stream can be redirected:

  .. code-block:: text

     $ uw config compare --file-1-path values1.nml --file-2-path values2.nml --verbose 2>compare.log

  The contents of ``compare.log``:

   .. code-block:: text

      [2024-01-08T16:59:20]    DEBUG Command: uw config compare --file-1-path values1.nml --file-2-path values2.nml --verbose
      [2024-01-08T16:59:20]     INFO - values1.nml
      [2024-01-08T16:59:20]     INFO + values2.nml
      [2024-01-08T16:59:20]     INFO ---------------------------------------------------------------------
      [2024-01-08T16:59:20]     INFO values:       recipient:  - None + World

.. note:: Comparisons are supported only for configs of the same format, e.g. YAML vs YAML, Fortran namelist vs Fortran namelist, etc. ``uw`` will flag invalid comparisons:

   .. code-block:: text

      $ uw config compare --file-1-path a.yaml --file-2-path b.nml
      [2024-01-23T23:21:37]    ERROR Formats do not match: yaml vs nml

.. _cli_config_realize_examples:

``realize``
-----------

In ``uw`` terminology, to realize a configuration file is to transform it from its raw form into its final, usable state. The ``realize`` action can build a complete config file from two or more separate files.

.. code-block:: text

   $ uw config realize --help
   usage: uw config realize [-h] [--version] [--input-file PATH] [--input-format {ini,nml,sh,yaml}]
                            [--update-file PATH] [--update-format {ini,nml,sh,yaml}]
                            [--output-file PATH] [--output-format {ini,nml,sh,yaml}]
                            [--output-block KEY[.KEY[.KEY]...]] [--values-needed] [--total]
                            [--dry-run] [--quiet] [--verbose]

   Realize config

   Optional arguments:
     -h, --help
         Show help and exit
     --version
         Show version info and exit
     --input-file PATH, -i PATH
         Path to input file (defaults to stdin)
     --input-format {ini,nml,sh,yaml}
         Input format
     --update-file PATH, -u PATH
         Path to update file (defaults to stdin)
     --update-format {ini,nml,sh,yaml}
         Input format
     --output-file PATH, -o PATH
         Path to output file (defaults to stdout)
     --output-format {ini,nml,sh,yaml}
         Output format
     --output-block KEY[.KEY[.KEY]...]
         Dot-separated path of keys to the block to be output
     --values-needed
         Print report of values needed to render template
     --total
         Require rendering of all Jinja2 variables/expressions
     --dry-run
         Only log info, making no changes
     --quiet, -q
         Print no logging messages
     --verbose, -v
         Print all logging messages

Examples
^^^^^^^^

The initial examples in this section use YAML file ``config.yaml`` with the following contents:

.. code-block:: yaml

   values:
     date: '{{ yyyymmdd }}'
     empty:
     greeting: Hello
     message: '{{ ((greeting + " " + recipient + " ") * repeat) | trim }}'
     recipient: World
     repeat: 1

and YAML file ``update.yaml`` with the following contents:

.. code-block:: yaml

   values:
     date: 20240105
     greeting: Good Night
     recipient: Moon
     repeat: 2

* To show the values in the input config file that have unrendered Jinja2 variables/expressions or empty keys:

  .. code-block:: text

     $ uw config realize --input-file config.yaml --output-format yaml --values-needed
     [2024-05-20T18:33:01]     INFO Keys that are complete:
     [2024-05-20T18:33:01]     INFO   values
     [2024-05-20T18:33:01]     INFO   values.greeting
     [2024-05-20T18:33:01]     INFO   values.message
     [2024-05-20T18:33:01]     INFO   values.recipient
     [2024-05-20T18:33:01]     INFO   values.repeat
     [2024-05-20T18:33:01]     INFO
     [2024-05-20T18:33:01]     INFO Keys with unrendered Jinja2 variables/expressions:
     [2024-05-20T18:33:01]     INFO   values.date: {{ yyyymmdd }}
     [2024-05-20T18:33:01]     INFO
     [2024-05-20T18:33:01]     INFO Keys that are set to empty:
     [2024-05-20T18:33:01]     INFO   values.empty

* To realize the config to ``stdout``, tghe output format must be explicitly specified:

  .. code-block:: text

     $ uw config realize --input-file config.yaml --output-format yaml
     values:
       date: '{{ yyyymmdd }}'
       empty: null
       greeting: Hello
       message: Hello World
       recipient: World
       repeat: 1

  Shell redirection via ``|``, ``>``, et al. may also be used to stream output to a file, another process, etc.

* Values in the input file can be updates via an optional update file:

  .. code-block:: text

     $ uw config realize --input-file config.yaml --update-file update.yaml --output-format yaml
     values:
       date: 20240105
       empty: null
       greeting: Good Night
       message: Good Night Moon Good Night Moon
       recipient: Moon
       repeat: 2

* To realize the config to a file via command-line argument:

  .. code-block:: text

     $ uw config realize --input-file config.yaml --update-file update.yaml --output-file realized.yaml

  The contents of ``realized.yaml``:

  .. code-block:: yaml

     values:
       date: 20240105
       empty: null
       greeting: Good Night
       message: Good Night Moon Good Night Moon
       recipient: Moon
       repeat: 2

* With the ``--dry-run`` flag specified, nothing is written to ``stdout`` (or to a file if ``--output-file`` is specified), but a report of what would have been written is logged to ``stderr``:

  .. code-block:: text

     $ uw config realize --input-file config.yaml --update-file update.yaml --output-file realized.yaml --dry-run
     [2024-05-20T19:05:55]     INFO values:
     [2024-05-20T19:05:55]     INFO   date: 20240105
     [2024-05-20T19:05:55]     INFO   empty: null
     [2024-05-20T19:05:55]     INFO   greeting: Good Night
     [2024-05-20T19:05:55]     INFO   message: Good Night Moon Good Night Moon
     [2024-05-20T19:05:55]     INFO   recipient: Moon
     [2024-05-20T19:05:55]     INFO   repeat: 2

* If the config file has an unrecognized (or no) extension, ``uw`` will not automatically know how to parse its contents:

  .. code-block:: text

     $ uw config realize --input-file config.txt --update-file update.yaml --output-format yaml
     Cannot deduce format of 'config.txt' from unknown extension 'txt'

  The format can be explicitly specified  (``config.txt`` is a copy of ``config.yaml``):

  .. code-block:: text

     $ uw config realize --input-file config.txt --update-file update.yaml --output-format yaml --input-format yaml
     values:
       date: 20240105
       empty: null
       greeting: Good Night
       message: Good Night Moon Good Night Moon
       recipient: Moon
       repeat: 2

* Similarly, if an input file is read from ``stdin``, ``uw`` will not automatically know how to parse its contents:

  .. code-block:: text

     $ cat config.yaml | uw config realize --update-file update.yaml --output-format yaml
     Specify --input-format when --input-file is not specified

  The format can be explicitly specified  (``config.txt`` is a copy of ``config.yaml``):

  .. code-block:: text

     $ cat config.yaml | uw config realize --update-file update.yaml --output-format yaml --input-format yaml
     values:
       date: 20240105
       empty: null
       greeting: Good Night
       message: Good Night Moon Good Night Moon
       recipient: Moon
       repeat: 2

* This example demonstrates: 1. Reading a config from ``stdin``, 2. Extracting a specific subsection with the ``--output-block`` option, and 3. Writing the output in a different format:

  .. code-block:: text

     $ cat config.yaml | uw config realize --input-format yaml --update-file update.yaml --output-block values --output-format sh
     date=20240105
     empty=None
     greeting='Good Night'
     message='Good Night Moon Good Night Moon'
     recipient=Moon
     repeat=2

.. note:: Combining configs with incompatible depths is not supported. ``ini`` and ``nml`` configs are depth-2, as they organize their key-value pairs (one level) under top-level sections or namelists (a second level). ``sh`` configs are depth-1, and ``yaml`` configs have arbitrary depth.

   For example, when attempting to generate a ``sh`` config from the original depth-2 ``config.yaml``:

   .. code-block:: text

      $ uw config realize --input-file config.yaml --output-format sh
      [2024-05-20T19:17:02]    ERROR Cannot realize depth-2 config to type-'sh' config

* It is possible to provide update values, rather than the input config, on ``stdin``. Usage rules are as follows:

  * Only if either ``--update-file`` or ``--update-config`` are specified will ``uw`` attempt to read and apply update values to the input config.
  * If ``--update-file`` is provided with an unrecognized (or no) extension, or if the update values are provided on ``stdin``, ``--update-format`` must be used to specify the correct format.
  * At least one of the input config and the update config must be provided via file: They cannot be streamed from ``stdin`` simultaneously.

  For example, here the update config is provided on ``stdin`` and the input config is read from a file:

  .. code-block:: text

     $ echo "yyyymmdd: 20240520" | uw config realize --input-file config.yaml --update-format yaml --output-format yaml
     values:
       date: '20240520'
       empty: null
       greeting: Hello
       message: Hello World
       recipient: World
       repeat: 1
     yyyymmdd: 20240520

* By default, variables/expressions that cannot be rendered are passed through unchanged in the output. For example, given config file ``flowers.yaml`` with contents

  .. code-block:: yaml

     roses: "{{ color1 }}"
     violets: "{{ color2 }}"
     color1: red

  .. code-block:: text

     $ uw config realize --input-file flowers.yaml --output-format yaml
     roses: red
     violets: '{{ color2 }}'
     color1: red
     $ echo $?
     0

  Adding the ``--total`` flag, however, requires ``uw`` to totally realize the config, and to exit with error status if it cannot:

  .. code-block:: text

     $ uw config realize --input-file flowers.yaml --output-format yaml --total
     [2024-05-20T18:39:37]    ERROR Config could not be realized. Try with --values-needed for details.
     $ echo $?
     1

* Realization of individual values is all-or-nothing. If a single value contains a mix of renderable and unrenderable variables/expressions, then the entire value remains unrealized. For example, given ``flowers.yaml`` with contents

  .. code-block:: yaml

     roses: "{{ color1 }} or {{ color2 }}"
     color1: red

  .. code-block:: text

     $ uw config realize --input-file flowers.yaml --output-format yaml
     roses: '{{ color1 }} or {{ color2 }}'
     color1: red

* To request verbose log output:

  .. code-block:: text

     $ echo "{hello: '{{ recipient }}', recipient: world}" | uw config realize --input-format yaml --output-format yaml --verbose
     [2024-05-20T19:09:21]    DEBUG Command: uw config realize --input-format yaml --output-format yaml --verbose
     [2024-05-20T19:09:21]    DEBUG Reading input from stdin
     [2024-05-20T19:09:21]    DEBUG Dereferencing, current value:
     [2024-05-20T19:09:21]    DEBUG   hello: '{{ recipient }}'
     [2024-05-20T19:09:21]    DEBUG   recipient: world
     [2024-05-20T19:09:21]    DEBUG [dereference] Rendering: {{ recipient }}
     [2024-05-20T19:09:21]    DEBUG [dereference] Rendered: world
     [2024-05-20T19:09:21]    DEBUG [dereference] Rendering: hello
     [2024-05-20T19:09:21]    DEBUG [dereference] Rendered: hello
     [2024-05-20T19:09:21]    DEBUG [dereference] Rendering: world
     [2024-05-20T19:09:21]    DEBUG [dereference] Rendered: world
     [2024-05-20T19:09:21]    DEBUG [dereference] Rendering: recipient
     [2024-05-20T19:09:21]    DEBUG [dereference] Rendered: recipient
     [2024-05-20T19:09:21]    DEBUG Dereferencing, current value:
     [2024-05-20T19:09:21]    DEBUG   hello: world
     [2024-05-20T19:09:21]    DEBUG   recipient: world
     [2024-05-20T19:09:21]    DEBUG [dereference] Rendering: world
     [2024-05-20T19:09:21]    DEBUG [dereference] Rendered: world
     [2024-05-20T19:09:21]    DEBUG [dereference] Rendering: hello
     [2024-05-20T19:09:21]    DEBUG [dereference] Rendered: hello
     [2024-05-20T19:09:21]    DEBUG [dereference] Rendering: world
     [2024-05-20T19:09:21]    DEBUG [dereference] Rendered: world
     [2024-05-20T19:09:21]    DEBUG [dereference] Rendering: recipient
     [2024-05-20T19:09:21]    DEBUG [dereference] Rendered: recipient
     [2024-05-20T19:09:21]    DEBUG Dereferencing, final value:
     [2024-05-20T19:09:21]    DEBUG   hello: world
     [2024-05-20T19:09:21]    DEBUG   recipient: world
     [2024-05-20T19:09:21]    DEBUG Writing output to stdout
     hello: world
     recipient: world

  Note that ``uw`` logs to ``stderr`` and writes non-log output to ``stdout``, so the streams can be redirected separately:

  .. code-block:: text

     $ echo "{hello: '{{ recipient }}', recipient: world}" | uw config realize --input-format yaml --output-format yaml --verbose >realized.yaml 2>realized.log

  The contents of ``realized.yaml``:

  .. code-block:: yaml

     hello: world
     recipient: world

  The contents of ``realized.log``:

  .. code-block:: text

     [2024-05-20T19:10:11]    DEBUG Command: uw config realize --input-format yaml --output-format yaml --verbose
     [2024-05-20T19:10:11]    DEBUG Reading input from stdin
     [2024-05-20T19:10:11]    DEBUG Dereferencing, current value:
     [2024-05-20T19:10:11]    DEBUG   hello: '{{ recipient }}'
     [2024-05-20T19:10:11]    DEBUG   recipient: world
     [2024-05-20T19:10:11]    DEBUG [dereference] Rendering: {{ recipient }}
     [2024-05-20T19:10:11]    DEBUG [dereference] Rendered: world
     [2024-05-20T19:10:11]    DEBUG [dereference] Rendering: hello
     [2024-05-20T19:10:11]    DEBUG [dereference] Rendered: hello
     [2024-05-20T19:10:11]    DEBUG [dereference] Rendering: world
     [2024-05-20T19:10:11]    DEBUG [dereference] Rendered: world
     [2024-05-20T19:10:11]    DEBUG [dereference] Rendering: recipient
     [2024-05-20T19:10:11]    DEBUG [dereference] Rendered: recipient
     [2024-05-20T19:10:11]    DEBUG Dereferencing, current value:
     [2024-05-20T19:10:11]    DEBUG   hello: world
     [2024-05-20T19:10:11]    DEBUG   recipient: world
     [2024-05-20T19:10:11]    DEBUG [dereference] Rendering: world
     [2024-05-20T19:10:11]    DEBUG [dereference] Rendered: world
     [2024-05-20T19:10:11]    DEBUG [dereference] Rendering: hello
     [2024-05-20T19:10:11]    DEBUG [dereference] Rendered: hello
     [2024-05-20T19:10:11]    DEBUG [dereference] Rendering: world
     [2024-05-20T19:10:11]    DEBUG [dereference] Rendered: world
     [2024-05-20T19:10:11]    DEBUG [dereference] Rendering: recipient
     [2024-05-20T19:10:11]    DEBUG [dereference] Rendered: recipient
     [2024-05-20T19:10:11]    DEBUG Dereferencing, final value:
     [2024-05-20T19:10:11]    DEBUG   hello: world
     [2024-05-20T19:10:11]    DEBUG   recipient: world
     [2024-05-20T19:10:11]    DEBUG Writing output to stdout

.. _cli_config_validate_examples:

``validate``
------------

The ``validate`` action ensures that a given config file is structured properly.

.. code-block:: text

   $ uw config validate --help
   usage: uw config validate --schema-file PATH [-h] [--version] [--input-file PATH] [--quiet]
                             [--verbose]

   Validate config

   Required arguments:
     --schema-file PATH
         Path to schema file to use for validation

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

The examples that follow use the :json-schema:`JSON Schema<understanding-json-schema/reference>` file ``schema.jsonschema`` with the following contents:

.. code-block:: json

   {
     "$schema": "http://json-schema.org/draft-07/schema#",
     "type": "object",
     "properties": {
       "values": {
         "type": "object",
         "properties": {
           "greeting": {
             "type": "string"
           },
           "recipient": {
             "type": "string"
           }
         },
         "required": ["greeting", "recipient"],
         "additionalProperties": false
       }
     },
     "required": ["values"],
     "additionalProperties": false
   }

and the YAML file ``values.yaml`` with the following contents:

.. code-block:: yaml

   values:
     greeting: Hello
     recipient: World

* To validate a YAML config against a given JSON schema:

  .. code-block:: text

     $ uw config validate --schema-file schema.jsonschema --input-file values.yaml
     [2024-01-03T17:23:07]     INFO 0 UW schema-validation errors found

  Shell redirection via ``|``, ``>``, et al. may also be used to stream output to a file, another process, etc.

* To read the *config* from ``stdin`` and print validation results to ``stdout``:

  .. code-block:: text

     $ cat values.yaml | uw config validate --schema-file schema.jsonschema
     [2024-01-03T17:26:29]     INFO 0 UW schema-validation errors found

* However, reading the *schema* from ``stdin`` is **not** supported:

  .. code-block:: text

     $ cat schema.jsonschema | uw config validate --input-file values.yaml
     uw config validate: error: the following arguments are required: --schema-file

* If a config fails validation, differences from the schema will be displayed. For example, with ``recipient: World`` removed from ``values.yaml``:

  .. code-block:: text

     $ uw config validate --schema-file schema.jsonschema --input-file values.yaml
     [2024-01-03T17:31:19]    ERROR 1 UW schema-validation error found
     [2024-01-03T17:31:19]    ERROR 'recipient' is a required property
     [2024-01-03T17:31:19]    ERROR
     [2024-01-03T17:31:19]    ERROR Failed validating 'required' in schema['properties']['values']:
     [2024-01-03T17:31:19]    ERROR     {'additionalProperties': False,
     [2024-01-03T17:31:19]    ERROR      'properties': {'greeting': {'type': 'string'},
     [2024-01-03T17:31:19]    ERROR                     'recipient': {'type': 'string'}},
     [2024-01-03T17:31:19]    ERROR      'required': ['greeting', 'recipient'],
     [2024-01-03T17:31:19]    ERROR      'type': 'object'}
     [2024-01-03T17:31:19]    ERROR
     [2024-01-03T17:31:19]    ERROR On instance['values']:
     [2024-01-03T17:31:19]    ERROR     {'greeting': 'Hello'}

* To request verbose log output:

  .. code-block:: text

     $ uw config validate --schema-file schema.jsonschema --input-file values.yaml --verbose
     [2024-01-03T17:29:46]    DEBUG Command: uw config validate --schema-file schema.jsonschema --input-file values.yaml --verbose
     [2024-01-03T17:29:46]    DEBUG Dereferencing, initial value: {'values': {'greeting': 'Hello', 'recipient': 'World'}}
     [2024-01-03T17:29:46]    DEBUG Rendering: {'values': {'greeting': 'Hello', 'recipient': 'World'}}
     [2024-01-03T17:29:46]    DEBUG Rendering: {'greeting': 'Hello', 'recipient': 'World'}
     [2024-01-03T17:29:46]    DEBUG Rendering: Hello
     [2024-01-03T17:29:46]    DEBUG Rendering: World
     [2024-01-03T17:29:46]    DEBUG Dereferencing, final value: {'values': {'greeting': 'Hello', 'recipient': 'World'}}
     [2024-01-03T17:29:46]     INFO 0 UW schema-validation errors found

  Note that ``uw`` logs to ``stderr``, so the stream can be redirected:

  .. code-block:: text

     $ uw config validate --schema-file schema.jsonschema --input-file values.yaml --verbose 2>validate.log

  The contents of ``validate.log``:

  .. code-block:: text

     [2024-01-03T17:30:49]    DEBUG Command: uw config validate --schema-file schema.jsonschema --input-file values.yaml --verbose
     [2024-01-03T17:30:49]    DEBUG Dereferencing, initial value: {'values': {'greeting': 'Hello', 'recipient': 'World'}}
     [2024-01-03T17:30:49]    DEBUG Rendering: {'values': {'greeting': 'Hello', 'recipient': 'World'}}
     [2024-01-03T17:30:49]    DEBUG Rendering: {'greeting': 'Hello', 'recipient': 'World'}
     [2024-01-03T17:30:49]    DEBUG Rendering: Hello
     [2024-01-03T17:30:49]    DEBUG Rendering: World
     [2024-01-03T17:30:49]    DEBUG Dereferencing, final value: {'values': {'greeting': 'Hello', 'recipient': 'World'}}
     [2024-01-03T17:30:49]     INFO 0 UW schema-validation errors found
