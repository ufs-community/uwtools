streams:
^^^^^^^^

The ``streams:`` block comprises a mapping from stream names to sub-mappings providing configuration values for the named stream. See the "Configuring Model Input and Output" chapter in the *MPAS-Atmosphere Model User’s Guide*, available from the `MPAS releases page <https://mpas-dev.github.io/atmosphere/atmosphere_download>`_, for additional information, including the specifics of supported values, on these attributes.

**Required attributes:**

  ``filename_template:``

  The template for files that exist or will be created by the stream. (type: string)

  ``mutable:``

  Whether the set of fields that belong to the stream may be modified at model run-time. (type: boolean)

  ``type:``

  One of ``input``, ``output``, ``input;output``, or ``none``. (type: string)

**Optional attributes:**

  ``filename_interval:``

  The interval at which the stream will be read. (type: string)

  ``files:``

  Names of files, each of which lists variables, one per line, to associate with the stream. Each filename becomes a ``<file>`` child element of the current stream. (type: sequence of strings)

  ``input_interval:``

  The interval at which the stream will be read. Required if ``type:`` includes ``input``.  (type: string)

  ``output_interval:``

  The interval at which the stream will be written. Required if ``type:`` includes ``output``. (type: string)

  ``packages:``

  Packages attached to the stream. (type: semicolon-separated list of strings)

  ``streams:``

  Names of streams whose explicitly associated fields to associate with the current stream. Each named stream becomes a ``<stream>`` child element of the current stream. (type: sequence of strings)

  ``var_arrays:``

  Names of MPAS-defined ``var_array`` items whose constituent variables to associate with the current stream. Each named ``var_array`` becomes a ``<var_array>`` child element of the current stream. (type: sequence of strings)

  ``var_structs:``

  Names of MPAS-defined ``var_struct`` items whose variables to associate with the current stream. Each named ``var_struct`` becomes a ``<var_struct>`` child element of the current stream. (type: sequence of strings)

  ``vars:``

  Names of variables to associate with the current stream. Each named variable becomes a ``<var>`` child element of the current stream. (type: sequence of strings)
