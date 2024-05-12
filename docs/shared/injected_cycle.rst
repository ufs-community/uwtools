* This driver receives a ``cycle`` argument, which it makes available as a Python ``datetime`` object to Jinja2 when realizing its input config. This supports specification of cycle-specific values. For example, the key-value pair

  .. code-block:: yaml

     gfs.t{{ cycle.strftime('%H') }}z.atmanl.nc: /some/path/{{ cycle.strftime('%Y%m%d%H') }}/gfs.t{{ cycle.strftime('%H') }}z.atmanl.nc

  would be rendered as

  .. code-block:: yaml

     gfs.t18z.atmanl.nc: /some/path/2024021218/gfs.t18z.atmanl.nc

  for cycle ``2024-02-12T18``.
