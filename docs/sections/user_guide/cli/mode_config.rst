Mode ``config``
===============

The ``uw`` mode for handling configs.

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
      translate
          Translate configs
      validate
          Validate config

.. _compare_configs_cli_examples:

``compare``
-----------

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

The examples that follow use namelist files ``values1.nml`` and ``values2.nml``, both initially with content

.. code-block:: fortran

  &values
    greeting = "Hello"
    recipient = "World"
  /

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

* If a config file has an unrecognized (or no) extension, ``uw`` will not know how to parse its content:

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

  The content of ``compare.log``:

  .. code-block:: text

    [2024-01-08T16:59:20]    DEBUG Command: uw config compare --file-1-path values1.nml --file-2-path values2.nml --verbose
    [2024-01-08T16:59:20]     INFO - values1.nml
    [2024-01-08T16:59:20]     INFO + values2.nml
    [2024-01-08T16:59:20]     INFO ---------------------------------------------------------------------
    [2024-01-08T16:59:20]     INFO values:       recipient:  - None + World

.. _realize_configs_cli_examples:

``realize``
-----------

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

The examples that follow use YAML file ``config.yaml`` with content

.. code-block:: yaml

  values:
    greeting: Hello
    recipient: World
    message: '{{ (greeting + " " + recipient + " ") * repeat }}'
    date: '{{ yyyymmdd }}'
    repeat: 1
    empty:

supplemental YAML file ``values1.yaml`` with content

.. code-block:: yaml

  values:
    greeting: Good Night
    recipient: Moon
    date: 20240105
    repeat: 2

and additional supplemental YAML file ``values2.yaml`` with content

.. code-block:: yaml

  values:
    repeat: 5
    empty: false

* Show the values in the input config file that have unrendered Jinja2 variables/expressions or empty keys:

  .. code-block:: text

    $ uw config realize --input-file values.yaml --output-format yaml --values-needed
    [2024-01-05T11:34:22]     INFO Keys that are complete:
    [2024-01-05T11:34:22]     INFO     values
    [2024-01-05T11:34:22]     INFO     values.greeting
    [2024-01-05T11:34:22]     INFO     values.recipient
    [2024-01-05T11:34:22]     INFO     values.message
    [2024-01-05T11:34:22]     INFO     values.repeat
    [2024-01-05T11:34:22]     INFO
    [2024-01-05T11:34:22]     INFO Keys that have unfilled Jinja2 templates:
    [2024-01-05T11:34:22]     INFO     values.date: {{ yyyymmdd }}
    [2024-01-05T11:34:22]     INFO
    [2024-01-05T11:34:22]     INFO Keys that are set to empty:
    [2024-01-05T11:34:22]     INFO     values.empty

* To realize the config to ``stdout``, a target output format must be explicitly specified:

  .. code-block:: text

    $ uw config realize --input-file values.yaml --output-format yaml
    values:
      greeting: Hello
      recipient: World
      message: Hello World
      date: '{{ yyyymmdd }}'
      repeat: 1
      empty: null

  Shell redirection via ``|``, ``>``, et al may also be used to stream output to a file, another process, etc.

* Values in the primary input file can be overridden via one or more supplemental files specified as positional arguments, each overriding the last; or by environment variables, which have the highest precedence.

  .. code-block:: text

    $ recipient=Sun uw config realize --input-file values.yaml --output-format yaml supp.yaml config.yaml
    values:
      greeting: Good Night
      recipient: Moon
      message: Good Night Sun Good Night Sun
      date: 20240105
      repeat: 2
      empty: false

* Realize the config to a file via command-line argument:

  .. code-block:: text

    $ uw config realize --input-file values.yaml --output-file realized.yaml config.yaml

  The content of ``realized.yaml``:

  .. code-block:: yaml

    values:
      greeting: Good Night
      recipient: Moon
      message: Good Night Moon Good Night Moon
      date: 20240105
      repeat: 2
      empty: null

* With the ``--dry-run`` flag specified, nothing is written to ``stdout`` (or to a file if ``--output-file`` is specified), but a report of what would have been written is logged to ``stderr``:

  .. code-block:: text

    $ uw config realize --input-file values.yaml --output-file realized.yaml --dry-run config.yaml
    [2024-01-05T11:35:20]     INFO values:
    values:
      greeting: Good Night
      recipient: Moon
      message: Good Night Moon Good Night Moon
      date: 20240105
      repeat: 2
      empty: null

* If an input file is read alone from ``stdin``, ``uw`` will not know how to parse its content:

  .. code-block:: text

    $ cat values.yaml | uw config realize --output-file realized.yaml config.yaml
    Specify --input-format when --input-file is not specified

* Read the config from ``stdin`` and realize to ``stdout``:

  .. code-block:: text

    $ cat values.yaml | uw config realize --input-format yaml --output-format yaml config.yaml
    values:
      greeting: Good Night
      recipient: Moon
      message: Good Night Moon Good Night Moon
      date: 20240105
      repeat: 2
      empty: null

* If the config file has an unrecognized (or no) extension, ``uw`` will not know how to parse its content:

  .. code-block:: text

    $ uw config realize --input-file values.txt --output-format yaml config.yaml
    Cannot deduce format of 'values.txt' from unknown extension 'txt'

  In this case, the format can be explicitly specified:

  .. code-block:: text

    $ uw config realize --input-file values.txt --input-format yaml --output-format yaml config.yaml
    values:
      greeting: Good Night
      recipient: Moon
      message: Good Night Moon Good Night Moon
      date: 20240105
      repeat: 2
      empty: null

* Request verbose log output:

  .. code-block:: text

    $ uw config realize --input-file values.yaml --output-format yaml --verbose config.yaml
    [2024-01-05T11:37:23]    DEBUG Command: uw config realize --input-file values.yaml --output-format yaml --verbose config.yaml
    [2024-01-05T11:37:23]    DEBUG Before update, config has depth 2
    [2024-01-05T11:37:23]    DEBUG Supplemental config has depth 2
    [2024-01-05T11:37:23]    DEBUG After update, config has depth 2
    [2024-01-05T11:37:23]    DEBUG Dereferencing, initial value: {'values': {'greeting': 'Good Night', 'recipient': 'Moon', 'message': '{{ (greeting + " " + recipient + " ") * repeat }}', 'date': 20240105, 'repeat': 2, 'empty': None}}
    [2024-01-05T11:37:23]    DEBUG Rendering: {'values': {'greeting': 'Good Night', 'recipient': 'Moon', 'message': '{{ (greeting + " " + recipient + " ") * repeat }}', 'date': 20240105, 'repeat': 2, 'empty': None}}
    [2024-01-05T11:37:23]    DEBUG Rendering: {'greeting': 'Good Night', 'recipient': 'Moon', 'message': '{{ (greeting + " " + recipient + " ") * repeat }}', 'date': 20240105, 'repeat': 2, 'empty': None}
    [2024-01-05T11:37:23]    DEBUG Rendering: Good Night
    [2024-01-05T11:37:23]    DEBUG Rendering: Moon
    [2024-01-05T11:37:23]    DEBUG Rendering: {{ (greeting + " " + recipient + " ") * repeat }}
    [2024-01-05T11:37:23]    DEBUG Rendering: 20240105
    [2024-01-05T11:37:23]    DEBUG Rendered: 20240105
    [2024-01-05T11:37:23]    DEBUG Rendering: 2
    [2024-01-05T11:37:23]    DEBUG Rendered: 2
    [2024-01-05T11:37:23]    DEBUG Rendering: None
    [2024-01-05T11:37:23]    DEBUG Rendered: None
    [2024-01-05T11:37:23]    DEBUG Dereferencing, current value: {'values': {'greeting': 'Good Night', 'recipient': 'Moon', 'message': '{{ (greeting + " " + recipient + " ") * repeat }}', 'date': 20240105, 'repeat': 2, 'empty': None}}
    [2024-01-05T11:37:23]    DEBUG Rendering: {'values': {'greeting': 'Good Night', 'recipient': 'Moon', 'message': 'Good Night Moon Good Night Moon ', 'date': 20240105, 'repeat': 2, 'empty': None}}
    [2024-01-05T11:37:23]    DEBUG Rendering: {'greeting': 'Good Night', 'recipient': 'Moon', 'message': 'Good Night Moon Good Night Moon ', 'date': 20240105, 'repeat': 2, 'empty': None}
    [2024-01-05T11:37:23]    DEBUG Rendering: Good Night
    [2024-01-05T11:37:23]    DEBUG Rendering: Moon
    [2024-01-05T11:37:23]    DEBUG Rendering: Good Night Moon Good Night Moon
    [2024-01-05T11:37:23]    DEBUG Rendering: 20240105
    [2024-01-05T11:37:23]    DEBUG Rendered: 20240105
    [2024-01-05T11:37:23]    DEBUG Rendering: 2
    [2024-01-05T11:37:23]    DEBUG Rendered: 2
    [2024-01-05T11:37:23]    DEBUG Rendering: None
    [2024-01-05T11:37:23]    DEBUG Rendered: None
    [2024-01-05T11:37:23]    DEBUG Dereferencing, final value: {'values': {'greeting': 'Good Night', 'recipient': 'Moon', 'message': 'Good Night Moon Good Night Moon ', 'date': 20240105, 'repeat': 2, 'empty': None}}
    values:
      greeting: Good Night
      recipient: Moon
      message: Good Night Moon Good Night Moon
      date: 20240105
      repeat: 2
      empty: null

  Note that ``uw`` logs to ``stderr`` and writes non-log output to ``stdout``, so the streams can be redirected separately:

  .. code-block:: text

    $ uw config realize --input-file values.yaml --output-format yaml --verbose config.yaml >realized.yaml 2>realized.log

  The content of ``realized.yaml``:

  .. code-block:: yaml

    values:
      greeting: Good Night
      recipient: Moon
      message: Good Night Moon Good Night Moon
      date: 20240105
      repeat: 2
      empty: null

  The content of ``realized.log``:

  .. code-block:: text

    [2024-01-05T11:39:23]    DEBUG Command: uw config realize --input-file values.yaml --output-format yaml --verbose config.yaml
    [2024-01-05T11:39:23]    DEBUG Before update, config has depth 2
    [2024-01-05T11:39:23]    DEBUG Supplemental config has depth 2
    [2024-01-05T11:39:23]    DEBUG After update, config has depth 2
    [2024-01-05T11:39:23]    DEBUG Dereferencing, initial value: {'values': {'greeting': 'Good Night', 'recipient': 'Moon', 'message': '{{ (greeting + " " + recipient + " ") * repeat }}', 'date': 20240105, 'repeat': 2, 'empty': None}}
    [2024-01-05T11:39:23]    DEBUG Rendering: {'values': {'greeting': 'Good Night', 'recipient': 'Moon', 'message': '{{ (greeting + " " + recipient + " ") * repeat }}', 'date': 20240105, 'repeat': 2, 'empty': None}}
    [2024-01-05T11:39:23]    DEBUG Rendering: {'greeting': 'Good Night', 'recipient': 'Moon', 'message': '{{ (greeting + " " + recipient + " ") * repeat }}', 'date': 20240105, 'repeat': 2, 'empty': None}
    [2024-01-05T11:39:23]    DEBUG Rendering: Good Night
    [2024-01-05T11:39:23]    DEBUG Rendering: Moon
    [2024-01-05T11:39:23]    DEBUG Rendering: {{ (greeting + " " + recipient + " ") * repeat }}
    [2024-01-05T11:39:23]    DEBUG Rendering: 20240105
    [2024-01-05T11:39:23]    DEBUG Rendered: 20240105
    [2024-01-05T11:39:23]    DEBUG Rendering: 2
    [2024-01-05T11:39:23]    DEBUG Rendered: 2
    [2024-01-05T11:39:23]    DEBUG Rendering: None
    [2024-01-05T11:39:23]    DEBUG Rendered: None
    [2024-01-05T11:39:23]    DEBUG Dereferencing, current value: {'values': {'greeting': 'Good Night', 'recipient': 'Moon', 'message': '{{ (greeting + " " + recipient + " ") * repeat }}', 'date': 20240105, 'repeat': 2, 'empty': None}}
    [2024-01-05T11:39:23]    DEBUG Rendering: {'values': {'greeting': 'Good Night', 'recipient': 'Moon', 'message': 'Good Night Moon Good Night Moon ', 'date': 20240105, 'repeat': 2, 'empty': None}}
    [2024-01-05T11:39:23]    DEBUG Rendering: {'greeting': 'Good Night', 'recipient': 'Moon', 'message': 'Good Night Moon Good Night Moon ', 'date': 20240105, 'repeat': 2, 'empty': None}
    [2024-01-05T11:39:23]    DEBUG Rendering: Good Night
    [2024-01-05T11:39:23]    DEBUG Rendering: Moon
    [2024-01-05T11:39:23]    DEBUG Rendering: Good Night Moon Good Night Moon
    [2024-01-05T11:39:23]    DEBUG Rendering: 20240105
    [2024-01-05T11:39:23]    DEBUG Rendered: 20240105
    [2024-01-05T11:39:23]    DEBUG Rendering: 2
    [2024-01-05T11:39:23]    DEBUG Rendered: 2
    [2024-01-05T11:39:23]    DEBUG Rendering: None
    [2024-01-05T11:39:23]    DEBUG Rendered: None
    [2024-01-05T11:39:23]    DEBUG Dereferencing, final value: {'values': {'greeting': 'Good Night', 'recipient': 'Moon', 'message': 'Good Night Moon Good Night Moon ', 'date': 20240105, 'repeat': 2, 'empty': None}}

* It is important to note that ``uw`` does not allow invalid conversions.

  For example, when attempting to generate an ``sh`` config from a depth-2 ``yaml``:

  .. code-block:: text

    $ uw config realize --input-file values.yaml --output-format sh
    Cannot realize depth-2 config to type-'sh' config

  Note that ``ini`` and ``nml`` configs are, by definition, depth-2 configs, while ``sh`` configs are depth-1 and ``yaml`` configs have arbitrary depth.

.. _translate_configs_cli_examples:

``translate``
-------------

.. code-block:: text

  $ uw config translate --help
  usage: uw config translate [-h] [--input-file PATH] [--input-format {atparse}] [--output-file PATH] [--output-format {jinja2}] [--dry-run] [--quiet] [--verbose]

  Translate configs

  Optional arguments:
    -h, --help
          Show help and exit
    --input-file PATH, -i PATH
          Path to input file (defaults to stdin)
    --input-format {atparse}
          Input format
    --output-file PATH, -o PATH
          Path to output file (defaults to stdout)
    --output-format {jinja2}
          Output format
    --dry-run
          Only log info, making no changes
    --quiet, -q
          Print no logging messages
    --verbose, -v
          Print all logging messages

Examples
^^^^^^^^

The examples that follow use atparse-formatted template file ``atparse.txt`` with content

.. code-block:: text

  @[greeting], @[recipient]!

* Convert an atparse-formatted template file to Jinja2 format:

  .. code-block:: text

    $ uw config translate --input-file atparse.txt --input-format atparse --output-format jinja2
    {{greeting}}, {{recipient}}!

  Shell redirection via ``|``, ``>``, et al may also be used to stream output to a file, another process, etc.

* Convert the template to a file via command-line argument:

  .. code-block:: text

    $ uw config translate --input-file atparse.txt --input-format atparse --output-file jinja2.txt --output-format jinja2

  The content of ``jinja2.txt``:

  .. code-block:: jinja

    {{greeting}}, {{recipient}}!

* With the ``--dry-run`` flag specified, nothing is written to ``stdout`` (or to a file if ``--output-file`` is specified), but a report of what would have been written is logged to ``stderr``:

  .. code-block:: text

    $ uw config translate --input-file atparse.txt --input-format atparse --output-format jinja2 --dry-run
    [2024-01-03T16:41:13]     INFO {{greeting}}, {{recipient}}!


* If an input is read alone from ``stdin``, ``uw`` will not know how to parse its content as we must always specify the formats:

  .. code-block:: text

    $ cat atparse.txt | uw config translate --input-format atparse --output-format jinja2
    {{greeting}}, {{recipient}}!

.. _validate_configs_cli_examples:

``validate``
------------

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

The examples that follow use :json-schema:`JSON Schema<understanding-json-schema/reference>` file ``schema.jsonschema`` with content

.. code:: json

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

and YAML file ``values.yaml`` with content

.. code-block:: yaml

  values:
    greeting: Hello
    recipient: World

* Validate a YAML config against a given JSON schema:

  .. code-block:: text

    $ uw config validate --schema-file schema.jsonschema --input-file values.yaml
    [2024-01-03T17:23:07]     INFO 0 UW schema-validation errors found

  Shell redirection via ``|``, ``>``, et al may also be used to stream output to a file, another process, etc.

* Read the config from ``stdin`` and print validation results to ``stdout``:

  .. code-block:: text

    $ cat values.yaml | uw config validate --schema-file schema.jsonschema
    [2024-01-03T17:26:29]     INFO 0 UW schema-validation errors found

* However, reading the schema from ``stdin`` is **not** supported:

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

* Request verbose log output:

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

  The content of ``validate.log``:

  .. code-block:: text

    [2024-01-03T17:30:49]    DEBUG Command: uw config validate --schema-file schema.jsonschema --input-file values.yaml --verbose
    [2024-01-03T17:30:49]    DEBUG Dereferencing, initial value: {'values': {'greeting': 'Hello', 'recipient': 'World'}}
    [2024-01-03T17:30:49]    DEBUG Rendering: {'values': {'greeting': 'Hello', 'recipient': 'World'}}
    [2024-01-03T17:30:49]    DEBUG Rendering: {'greeting': 'Hello', 'recipient': 'World'}
    [2024-01-03T17:30:49]    DEBUG Rendering: Hello
    [2024-01-03T17:30:49]    DEBUG Rendering: World
    [2024-01-03T17:30:49]    DEBUG Dereferencing, final value: {'values': {'greeting': 'Hello', 'recipient': 'World'}}
    [2024-01-03T17:30:49]     INFO 0 UW schema-validation errors found
