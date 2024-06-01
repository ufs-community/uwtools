streams:
^^^^^^^^

See the "Configuring Model Input and Output" chapter in the _MPAS-Atmosphere Model User’s Guide_, available from the `MPAS releases page <https://mpas-dev.github.io/atmosphere/atmosphere_download>`_, for additional information, including the specifics of supported values, on these attributes..

**Required attributes:**

``filename_template:``

The template for files that exist or will be created by the stream. (type: string)

``mutable:``

Whether the set of fields that belong to the stream may be modified at model run-time. (type: boolean)

``name:``

A unique name used to refer to the stream. (type: string)

``type:``

One of ``input``, ``output``, ``input;output``, or ``none``. (type: string)

**Optional attributes:**

``filename_interval:``

The interval at which the stream will be read. (type: string)

``files:``

Names of files, each of which lists variables, one per line, to associate with the stream. (type: sequence of strings)

``input_interval:``

The interval at which the stream will be read. Required if ``type:`` includes ``input``.  (type: string)

``output_interval:``

The interval at which the stream will be written. Required if ``type:`` includes ``output``. (type: string)

``packages:``

Packages attached to the stream. (type: semicolon-separated list of strings)
