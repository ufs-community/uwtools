Mode ``config``
===============

The ``uw`` mode for handling configuration files (configs).

.. code-block:: text

   $ uw config --help
   usage: uw config [-h] MODE ...

   Handle configs

   Optional arguments:
     -h, --help
           Show help and exit

   Positional arguments:
     MODE
       compare
           Compare configs
       realize
           Realize config
       validate
           Validate config

.. _cli_config_compare_examples:

``compare``
-----------

The ``compare`` mode lets users compare two config files. 

.. code-block:: text

   $ uw config compare --help
   usage: uw config compare --file-1-path PATH --file-2-path PATH [-h]
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

Users have several options:

* Compare two config files with the same contents:

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

* Request verbose log output:

  .. code-block:: text

     $ uw config compare --file-1-path values1.nml --file-2-path values2.nml --verbose
     [2024-01-08T16:57:28]    DEBUG Command: uw config compare --file-1-path values1.nml --file-2-path values2.nml --verbose
     [2024-01-08T16:57:28]     INFO - values1.nml
     [2024-01-08T16:57:28]     INFO + values2.nml
     [2024-01-08T16:57:28]     INFO ---------------------------------------------------------------------
     [2024-01-08T16:57:28]     INFO values:       recipient:  - None + World

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

.. _cli_config_realize_examples:

``realize``
-----------

In ``uw`` terminology, to realize a configuration file is to transform it from its raw form into its final, usable state. The ``realize`` mode can build a complete config file from two or more separate files. 

.. code-block:: text

  $ uw config realize --help
  usage: uw config realize --values-file PATH [-h] [--input-file PATH]
                           [--input-format {ini,nml,sh,yaml}] [--output-file PATH]
                           [--output-format {ini,nml,sh,yaml}] [--values-format {ini,nml,sh,yaml}]
                           [--values-needed] [--dry-run] [--quiet] [--verbose]

  Realize config

  Required arguments:
    --values-file PATH
          Path to file providing override or interpolation values

  Optional arguments:
    -h, --help
          Show help and exit
    --input-file PATH, -i PATH
          Path to input file (defaults to stdin)
    --input-format {ini,nml,sh,yaml}
          Input format
    --output-file PATH, -o PATH
          Path to output file (defaults to stdout)
    --output-format {ini,nml,sh,yaml}
          Output format
    --values-format {ini,nml,sh,yaml}
          Values format
    --values-needed
          Print report of values needed to render template
    --dry-run
          Only log info, making no changes
    --quiet, -q
          Print no logging messages
    --verbose, -v
          Print all logging messages

Examples
^^^^^^^^

The examples in this section use the YAML file ``config.yaml`` with the following contents:

.. code-block:: yaml

   values:
     date: '{{ yyyymmdd }}'
     empty:
     greeting: Hello
     message: '{{ (greeting + " " + recipient + " ") * repeat }}'
     recipient: World
     repeat: 1

and the supplemental YAML file ``values1.yaml`` with the following contents:

.. code-block:: yaml

   values:
     date: 20240105
     greeting: Good Night
     recipient: Moon
     repeat: 2

and an additional supplemental YAML file ``values2.yaml`` with the following contents:

.. code-block:: yaml

   values:
     empty: false
     repeat: 3

* To show the values in the input config file that have unrendered Jinja2 variables/expressions or empty keys:

  .. code-block:: text

     $ uw config realize --input-file config.yaml --output-format yaml --values-needed
     [2024-01-10T21:29:20]     INFO Keys that are complete:
     [2024-01-10T21:29:20]     INFO     values
     [2024-01-10T21:29:20]     INFO     values.greeting
     [2024-01-10T21:29:20]     INFO     values.message
     [2024-01-10T21:29:20]     INFO     values.recipient
     [2024-01-10T21:29:20]     INFO     values.repeat
     [2024-01-10T21:29:20]     INFO
     [2024-01-10T21:29:20]     INFO Keys with unrendered Jinja2 variables/expressions:
     [2024-01-10T21:29:20]     INFO     values.date: {{ yyyymmdd }}
     [2024-01-10T21:29:20]     INFO
     [2024-01-10T21:29:20]     INFO Keys that are set to empty:
     [2024-01-10T21:29:20]     INFO     values.empty

* To realize the config to ``stdout``, a target output format must be explicitly specified:

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

* Values in the primary input file can be overridden via one or more supplemental files specified as positional arguments, each overriding the last, or by environment variables, which have the highest precedence.

  .. code-block:: text

     $ recipient=Sun uw config realize --input-file config.yaml --output-format yaml values1.yaml values2.yaml
     values:
       date: 20240105
       empty: false
       greeting: Good Night
       message: Good Night Sun Good Night Sun Good Night Sun
       recipient: Moon
       repeat: 3

* To realize the config to a file via command-line argument:

  .. code-block:: text

     $ uw config realize --input-file config.yaml --output-file realized.yaml values1.yaml

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

     $ uw config realize --input-file config.yaml --output-file realized.yaml --dry-run values1.yaml
     [2024-01-10T21:38:32]     INFO values:
     [2024-01-10T21:38:32]     INFO   date: 20240105
     [2024-01-10T21:38:32]     INFO   empty: null
     [2024-01-10T21:38:32]     INFO   greeting: Good Night
     [2024-01-10T21:38:32]     INFO   message: Good Night Moon Good Night Moon
     [2024-01-10T21:38:32]     INFO   recipient: Moon
     [2024-01-10T21:38:32]     INFO   repeat: 2

* If an input file is read alone from ``stdin``, ``uw`` will not know how to parse its contents:

  .. code-block:: text

     $ cat config.yaml | uw config realize --output-file realized.yaml values1.yaml
     Specify --input-format when --input-file is not specified

* To read the config from ``stdin`` and realize to ``stdout``:

  .. code-block:: text

     $ cat config.yaml | uw config realize --input-format yaml --output-format yaml values1.yaml
     values:
       date: 20240105
       empty: null
       greeting: Good Night
       message: Good Night Moon Good Night Moon
       recipient: Moon
       repeat: 2

* If the config file has an unrecognized (or no) extension, ``uw`` will not know how to parse its contents:

  .. code-block:: text

     $ uw config realize --input-file config.txt --output-format yaml values1.yaml
     Cannot deduce format of 'config.txt' from unknown extension 'txt'

  In this case, the format can be explicitly specified  (``config.txt`` is a copy of ``config.yaml``):

  .. code-block:: text

     $ uw config realize --input-file config.txt --input-format yaml --output-format yaml values1.yaml
     values:
       date: 20240105
       empty: null
       greeting: Good Night
       message: Good Night Moon Good Night Moon
       recipient: Moon
       repeat: 2

* To request verbose log output:

  .. code-block:: text

     $ uw config realize --input-file config.yaml --output-format yaml --verbose values1.yaml
     [2024-01-10T21:42:17]    DEBUG Command: uw config realize --input-file config.yaml --output-format yaml --verbose values1.yaml
     [2024-01-10T21:42:17]    DEBUG Before update, config has depth 2
     [2024-01-10T21:42:17]    DEBUG Supplemental config has depth 2
     [2024-01-10T21:42:17]    DEBUG After update, config has depth 2
     [2024-01-10T21:42:17]    DEBUG Dereferencing, initial value: {'values': {'date': 20240105, 'empty': None, 'greeting': 'Good Night', 'message': '{{ (greeting + " " + recipient + " ") * repeat }}', 'recipient': 'Moon', 'repeat': 2}}
     [2024-01-10T21:42:17]    DEBUG Rendering: {'values': {'date': 20240105, 'empty': None, 'greeting': 'Good Night', 'message': '{{ (greeting + " " + recipient + " ") * repeat }}', 'recipient': 'Moon', 'repeat': 2}}
     [2024-01-10T21:42:17]    DEBUG Rendering: {'date': 20240105, 'empty': None, 'greeting': 'Good Night', 'message': '{{ (greeting + " " + recipient + " ") * repeat }}', 'recipient': 'Moon', 'repeat': 2}
     [2024-01-10T21:42:17]    DEBUG Rendering: 20240105
     [2024-01-10T21:42:17]    DEBUG Rendered: 20240105
     [2024-01-10T21:42:17]    DEBUG Rendering: None
     [2024-01-10T21:42:17]    DEBUG Rendered: None
     [2024-01-10T21:42:17]    DEBUG Rendering: Good Night
     [2024-01-10T21:42:17]    DEBUG Rendering: {{ (greeting + " " + recipient + " ") * repeat }}
     [2024-01-10T21:42:17]    DEBUG Rendering: Moon
     [2024-01-10T21:42:17]    DEBUG Rendering: 2
     [2024-01-10T21:42:17]    DEBUG Rendered: 2
     [2024-01-10T21:42:17]    DEBUG Dereferencing, current value: {'values': {'date': 20240105, 'empty': None, 'greeting': 'Good Night', 'message': '{{ (greeting + " " + recipient + " ") * repeat }}', 'recipient': 'Moon', 'repeat': 2}}
     [2024-01-10T21:42:17]    DEBUG Rendering: {'values': {'date': 20240105, 'empty': None, 'greeting': 'Good Night', 'message': 'Good Night Moon Good Night Moon', 'recipient': 'Moon', 'repeat': 2}}
     [2024-01-10T21:42:17]    DEBUG Rendering: {'date': 20240105, 'empty': None, 'greeting': 'Good Night', 'message': 'Good Night Moon Good Night Moon', 'recipient': 'Moon', 'repeat': 2}
     [2024-01-10T21:42:17]    DEBUG Rendering: 20240105
     [2024-01-10T21:42:17]    DEBUG Rendered: 20240105
     [2024-01-10T21:42:17]    DEBUG Rendering: None
     [2024-01-10T21:42:17]    DEBUG Rendered: None
     [2024-01-10T21:42:17]    DEBUG Rendering: Good Night
     [2024-01-10T21:42:17]    DEBUG Rendering: Good Night Moon Good Night Moon
     [2024-01-10T21:42:17]    DEBUG Rendering: Moon
     [2024-01-10T21:42:17]    DEBUG Rendering: 2
     [2024-01-10T21:42:17]    DEBUG Rendered: 2
     [2024-01-10T21:42:17]    DEBUG Dereferencing, final value: {'values': {'date': 20240105, 'empty': None, 'greeting': 'Good Night', 'message': 'Good Night Moon Good Night Moon', 'recipient': 'Moon', 'repeat': 2}}
     values:
       date: 20240105
       empty: null
       greeting: Good Night
       message: Good Night Moon Good Night Moon
       recipient: Moon
       repeat: 2

  Note that ``uw`` logs to ``stderr`` and writes non-log output to ``stdout``, so the streams can be redirected separately:

  .. code-block:: text

     $ uw config realize --input-file config.yaml --output-format yaml --verbose values1.yaml >realized.yaml 2>realized.log

  The contents of ``realized.yaml``:

  .. code-block:: yaml

     values:
       date: 20240105
       empty: null
       greeting: Good Night
       message: Good Night Moon Good Night Moon
       recipient: Moon
       repeat: 2

  The contents of ``realized.log``:

  .. code-block:: text

     [2024-01-10T21:43:58]    DEBUG Command: uw config realize --input-file config.yaml --output-format yaml --verbose values1.yaml
     [2024-01-10T21:43:58]    DEBUG Before update, config has depth 2
     [2024-01-10T21:43:58]    DEBUG Supplemental config has depth 2
     ...
     [2024-01-10T21:43:58]    DEBUG Rendering: 2
     [2024-01-10T21:43:58]    DEBUG Rendered: 2
     [2024-01-10T21:43:58]    DEBUG Dereferencing, final value: {'values': {'date': 20240105, 'empty': None, 'greeting': 'Good Night', 'message': 'Good Night Moon Good Night Moon', 'recipient': 'Moon', 'repeat': 2}}

.. note::

   Note that ``uw`` does not allow invalid conversions. For example, when attempting to generate a ``sh`` config from a depth-2 ``yaml``:

   .. code-block:: text

      $ uw config realize --input-file config.yaml --output-format sh
      [2024-01-10T21:46:00]    ERROR Cannot realize depth-2 config to type-'sh' config
      Cannot realize depth-2 config to type-'sh' config

   Note that ``ini`` and ``nml`` configs are, by definition, depth-2 configs, while ``sh`` configs are depth-1 and ``yaml`` configs have arbitrary depth.

.. _cli_config_validate_examples:

``validate``
------------

The ``validate`` mode ensures that a given config file is structured properly.

.. code-block:: text

   $ uw config validate --help
   usage: uw config validate --schema-file PATH [-h] [--input-file PATH] [--quiet] [--verbose]

   Validate config

   Required arguments:
     --schema-file PATH
         Path to schema file to use for validation

   Optional arguments:
     -h, --help
         Show help and exit
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
