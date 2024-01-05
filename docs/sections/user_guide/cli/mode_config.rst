Mode ``config``
===============

The ``uw`` mode for handling configs.

.. code:: sh

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

.. code:: sh

  $ uw config compare --help
  usage: uw config compare --file-1-path PATH --file-2-path PATH [-h] [--file-1-format {ini,nml,sh,yaml}] [--file-2-format {ini,nml,sh,yaml}] [--quiet] [--verbose]

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
~~~~~~~~

The examples that follow use namelist files ``values.nml`` and ``values2.nml`` with content

.. code:: sh

  &values
    greeting = "Hello"
    recipient = "World"
  /


* Compare two config files with the same contents:

  .. code:: sh

    $ uw config compare --file-1-path values.mml --file-2-path values2.nml
    [2024-01-03T16:20:46]     INFO - values.nml
    [2024-01-03T16:20:46]     INFO + values2.nml
    [2024-01-03T16:20:46]     INFO ---------------------------------------------------------------------


* If there are differences between the config files, they will be shown below the dashed line. For example, with ``recipient: World`` removed from ``values.nml``:

  .. code:: sh

    [2024-01-03T16:23:29]     INFO - values.nml
    [2024-01-03T16:23:29]     INFO + values2.nml
    [2024-01-03T16:23:29]     INFO ---------------------------------------------------------------------
    [2024-01-03T16:23:29]     INFO values:       recipient:  - None + World


* If a config file has an unrecognized (or no) extension, ``uw`` will not know how to parse its content:

  .. code:: sh

    $ uw config compare --file-1-path values.txt --file-2-path values.nml
    Cannot deduce format of 'values.txt' from unknown extension 'txt'

  In this case, the format can be explicitly specified:

  .. code:: sh

    $ uw config compare --file-1-path values.txt --file-1-format nml --file-2-path values.nml
    [2024-01-03T16:33:19]     INFO - values.txt
    [2024-01-03T16:33:19]     INFO + values.nml
    [2024-01-03T16:33:19]     INFO ---------------------------------------------------------------------
    [2024-01-03T16:33:19]     INFO values:       recipient:  - None + World

* Request verbose log output:

  .. code:: sh

    $ uw config compare --file-1-path values.nml --file-2-path values2.nml --verbose
    [2024-01-03T16:25:47]    DEBUG Command: uw config compare --file-1-path values.nml --file-2-path values2.nml --verbose
    [2024-01-03T16:25:47]     INFO - values.nml
    [2024-01-03T16:25:47]     INFO + values2.nml
    [2024-01-03T16:25:47]     INFO ---------------------------------------------------------------------
    [2024-01-03T16:25:47]     INFO values:       recipient:  - None + World

  Note that ``uw`` logs to ``stderr``, so the stream can be redirected:

  .. code:: sh

    $ uw config compare --file-1-path values.nml --file-2-path values2.nml --verbose 2>compare.log

  The content of ``compare.log``:

  .. code:: sh

    [2024-01-03T16:26:18]    DEBUG Command: uw config compare --file-1-path values.nml --file-2-path values2.nml --verbose
    [2024-01-03T16:26:18]     INFO - values.mml
    [2024-01-03T16:26:18]     INFO + values2.nml
    [2024-01-03T16:26:18]     INFO ---------------------------------------------------------------------
    [2024-01-03T16:26:18]     INFO values:       recipient:  - None + World

.. _realize_configs_cli_examples:

``realize``
-----------

.. code:: sh

  $ uw config realize --help
  usage: uw config realize --values-file PATH [-h] [--input-file PATH] [--input-format {ini,nml,sh,yaml}] [--output-file PATH] [--output-format {ini,nml,sh,yaml}] [--values-format {ini,nml,sh,yaml}]
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
~~~~~~~~

The examples that follow use YAML file ``values.yaml`` with content

.. code:: sh

  values:
    greeting: Hello
    recipient: World
    date: '{{ yyyymmdd }}'
    empty:

and supplemental YAML file ``supp.yaml`` with content

.. code:: sh

  values:
    greeting: Good Night
    recipient: Moon

* Show the values in the input config file that have unfilled Jinja2 templates or empty keys:

  .. code:: sh

    $ uw config realize --input-file values.yaml --output-format yaml --values-needed
    [2024-01-03T15:35:29]     INFO Keys that are complete:
    [2024-01-03T15:35:29]     INFO     values
    [2024-01-03T15:35:29]     INFO     values.greeting
    [2024-01-03T15:35:29]     INFO     values.recipient
    [2024-01-03T15:35:29]     INFO 
    [2024-01-03T15:35:29]     INFO Keys that have unfilled Jinja2 templates:
    [2024-01-03T15:35:29]     INFO     values.date: {{ yyyymmdd }}
    [2024-01-03T15:35:29]     INFO 
    [2024-01-03T15:35:29]     INFO Keys that are set to empty:
    [2024-01-03T15:35:29]     INFO     values.empty

* To realize the config to ``stdout``, a target output format must be explicitly specified:

  .. code:: sh

    $ uw config realize --input-file values.yaml --output-format yaml
    values:
      greeting: Hello
      recipient: World
      date: '{{ yyyymmdd }}'
      empty: null

  Shell redirection via ``|``, ``>``, et al may also be used to stream output to a file, another process, etc.

* Existing values can be overwritten and Jinja2 variables can be filled in by appending supplemental files to the end of the argument:

  .. code:: sh

    $ uw config realize --input-file values.yaml --output-format yaml supp.yaml
    values:
      greeting: Good Night
      recipient: Moon
      date: '{{ yyyymmdd }}'
      empty: null

* Realize the config to a file via command-line argument:

  .. code:: sh

    $ uw config realize --input-file values.yaml --output-file realized.yaml

  The content of ``realized.yaml``:

  .. code:: sh

      values:
        greeting: Hello
        recipient: World
        date: '{{ yyyymmdd }}'
        empty: null

* With the ``--dry-run`` flag specified, nothing is written to ``stdout`` (or to a file if ``--output-file`` is specified), but a report of what would have been written is logged to ``stderr``:

  .. code:: sh

    $ uw config realize --input-file values.yaml --output-file realized.yaml --dry-run
    [2024-01-03T15:39:23]     INFO values:
      greeting: Hello
      recipient: World
      date: '{{ yyyymmdd }}'
      empty: null


* If an input file is read alone from ``stdin``, ``uw`` will not know how to parse its content:

  .. code:: sh

    $ cat values.yaml | uw config realize --output-file realized.yaml
    Specify --input-format when --input-file is not specified

* Read the config from ``stdin`` and realize to ``stdout``:

  .. code:: sh

    $ cat values.yaml | uw config realize --input-format yaml --output-format yaml
    values:
      greeting: Hello
      recipient: World
      date: '{{ yyyymmdd }}'
      empty: null


* If the config file has an unrecognized (or no) extension, ``uw`` will not know how to parse its content:

  .. code:: sh

    $ uw config realize --input-file values.txt --output-format yaml
    Cannot deduce format of 'values.txt' from unknown extension 'txt'

  In this case, the format can be explicitly specified:

  .. code:: sh

    $ uw config realize --input-file values.txt --input-format yaml --output-format yaml
    values:
      greeting: Hello
      recipient: World
      date: '{{ yyyymmdd }}'
      empty: null


* Request verbose log output:

  .. code:: sh

    $ uw config realize --input-file values.yaml --output-format yaml --verbose
    [2024-01-03T15:56:28]    DEBUG Command: uw config realize --input-file values.yaml --output-format yaml --verbose
    [2024-01-03T15:56:28]    DEBUG Dereferencing, initial value: {'values': {'greeting': 'Hello', 'recipient': 'World', 'date': '{{ yyyymmdd }}', 'empty': None}}
    [2024-01-03T15:56:28]    DEBUG Rendering: {'values': {'greeting': 'Hello', 'recipient': 'World', 'date': '{{ yyyymmdd }}', 'empty': None}}
    [2024-01-03T15:56:28]    DEBUG Rendering: {'greeting': 'Hello', 'recipient': 'World', 'date': '{{ yyyymmdd }}', 'empty': None}
    [2024-01-03T15:56:28]    DEBUG Rendering: Hello
    [2024-01-03T15:56:28]    DEBUG Rendering: World
    [2024-01-03T15:56:28]    DEBUG Rendering: {{ yyyymmdd }}
    [2024-01-03T15:56:28]    DEBUG Rendering ERROR: 'yyyymmdd' is undefined
    [2024-01-03T15:56:28]    DEBUG Rendering: None
    [2024-01-03T15:56:28]    DEBUG Rendered: None
    [2024-01-03T15:56:28]    DEBUG Dereferencing, final value: {'values': {'greeting': 'Hello', 'recipient': 'World', 'date': '{{ yyyymmdd }}', 'empty': None}}
    values:
      greeting: Hello
      recipient: World
      date: '{{ yyyymmdd }}'
      empty: null

  Note that ``uw`` logs to ``stderr`` and writes non-log output to ``stdout``, so the streams can be redirected separately:

  .. code:: sh

    $ uw config realize --input-file values.yaml --output-format yaml --verbose >realized.yaml 2>realized.log

  The content of ``realized.yaml``:

  .. code:: sh

    values:
      greeting: Hello
      recipient: World
      date: '{{ yyyymmdd }}'
      empty: null

  The content of ``realized.log``:

  .. code:: sh

    [2024-01-03T15:58:07]    DEBUG Command: uw config realize --input-file values.yaml --output-format yaml --verbose
    [2024-01-03T15:58:07]    DEBUG Dereferencing, initial value: {'values': {'greeting': 'Hello', 'recipient': 'World', 'date': '{{ yyyymmdd }}', 'empty': None}}
    [2024-01-03T15:58:07]    DEBUG Rendering: {'values': {'greeting': 'Hello', 'recipient': 'World', 'date': '{{ yyyymmdd }}', 'empty': None}}
    [2024-01-03T15:58:07]    DEBUG Rendering: {'greeting': 'Hello', 'recipient': 'World', 'date': '{{ yyyymmdd }}', 'empty': None}
    [2024-01-03T15:58:07]    DEBUG Rendering: Hello
    [2024-01-03T15:58:07]    DEBUG Rendering: World
    [2024-01-03T15:58:07]    DEBUG Rendering: {{ yyyymmdd }}
    [2024-01-03T15:58:07]    DEBUG Rendering ERROR: 'yyyymmdd' is undefined
    [2024-01-03T15:58:07]    DEBUG Rendering: None
    [2024-01-03T15:58:07]    DEBUG Rendered: None
    [2024-01-03T15:58:07]    DEBUG Dereferencing, final value: {'values': {'greeting': 'Hello', 'recipient': 'World', 'date': '{{ yyyymmdd }}', 'empty': None}}

* It is important to note that ``uw`` does not allow invalid conversions. 

  For example, when attempting to generate an ``sh`` config from a depth-2 ``yaml``:

  .. code:: sh

    $ uw config realize --input-file values.yaml --output-format sh
    Cannot realize depth-2 config to type-'sh' config

  Note that ``ini`` and ``nml`` configs are, by definition, depth-2 configs, while ``sh`` configs are depth-1 and ``yaml`` configs have arbitrary depth.

.. _translate_configs_cli_examples:

``translate``
-------------

.. code:: sh

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
~~~~~~~~

The examples that follow use atparse-formatted template file ``atparse.txt`` with content

.. code:: sh

  @[greeting], @[recipient]!

* Convert an atparse-formatted template file to Jinja2 format:

  .. code:: sh

    $ uw config translate --input-file atparse.txt --input-format atparse --output-format jinja2
    {{greeting}}, {{recipient}}!

  Shell redirection via ``|``, ``>``, et al may also be used to stream output to a file, another process, etc.

* Convert the template to a file via command-line argument:

  .. code:: sh

    $ uw config translate --input-file atparse.txt --input-format atparse --output-file jinja2.txt --output-format jinja2

  The content of ``jinja2.txt``:

  .. code:: sh

    {{greeting}}, {{recipient}}!

* With the ``--dry-run`` flag specified, nothing is written to ``stdout`` (or to a file if ``--output-file`` is specified), but a report of what would have been written is logged to ``stderr``:

  .. code:: sh

    $ uw config translate --input-file atparse.txt --input-format atparse --output-format jinja2 --dry-run
    [2024-01-03T16:41:13]     INFO {{greeting}}, {{recipient}}!


* If an input is read alone from ``stdin``, ``uw`` will not know how to parse its content as we must always specify the formats:

  .. code:: sh

    $ cat atparse.txt | uw config translate --input-format atparse --output-format jinja2
    {{greeting}}, {{recipient}}!


.. _validate_configs_cli_examples:

``validate``
------------

.. code:: sh

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
~~~~~~~~

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

.. code:: sh

  values:
    greeting: Hello
    recipient: World

* Validate a YAML config against a given JSON schema:

  .. code:: sh

    $ uw config validate --schema-file schema.jsonschema --input-file values.yaml
    [2024-01-03T17:23:07]     INFO 0 UW schema-validation errors found

  Shell redirection via ``|``, ``>``, et al may also be used to stream output to a file, another process, etc.


* Read the config from ``stdin`` and print validation results to ``stdout``:

  .. code:: sh

    $ cat values.yaml | uw config validate --schema-file schema.jsonschema
    [2024-01-03T17:26:29]     INFO 0 UW schema-validation errors found


* However, reading the schema from ``stdin`` is **not** supported:

  .. code:: sh

    $ cat schema.jsonschema | uw config validate --input-file values.yaml
    uw config validate: error: the following arguments are required: --schema-file

* If a config fails validation, differences from the schema will be displayed. For example, with ``recipient: World`` removed from ``values.yaml``:

  .. code:: sh

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

  .. code:: sh

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

  .. code:: sh

    $ uw config validate --schema-file schema.jsonschema --input-file values.yaml --verbose 2>validate.log

  The content of ``validate.log``:

  .. code:: sh

    [2024-01-03T17:30:49]    DEBUG Command: uw config validate --schema-file schema.jsonschema --input-file values.yaml --verbose
    [2024-01-03T17:30:49]    DEBUG Dereferencing, initial value: {'values': {'greeting': 'Hello', 'recipient': 'World'}}
    [2024-01-03T17:30:49]    DEBUG Rendering: {'values': {'greeting': 'Hello', 'recipient': 'World'}}
    [2024-01-03T17:30:49]    DEBUG Rendering: {'greeting': 'Hello', 'recipient': 'World'}
    [2024-01-03T17:30:49]    DEBUG Rendering: Hello
    [2024-01-03T17:30:49]    DEBUG Rendering: World
    [2024-01-03T17:30:49]    DEBUG Dereferencing, final value: {'values': {'greeting': 'Hello', 'recipient': 'World'}}
    [2024-01-03T17:30:49]     INFO 0 UW schema-validation errors found
