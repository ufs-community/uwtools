* This driver receives a ``leadtime`` argument, which it makes available as a Python ``timedelta`` object to Jinja2 when realizing its input config. This supports specification of leadtime-specific values. For example, the key-value pairs

  .. code-block:: yaml

     datestr: "{{ (cycle + leadtime).strftime('%Y-%m-%d_%H:%M:%S') }}"
     suffix: f{{ '%03d' % (leadtime.total_seconds() / 3600) }}

  would be rendered as

  .. code-block:: yaml

     datestr: 2024-05-09_06:00:00
     suffix: f018

  for cycle ``2024-05-08T12`` and leadtime ``18``.
