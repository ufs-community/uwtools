* This driver receives a ``leadtime`` argument, which it makes available as a Python ``timedelta`` object to Jinja2 when realizing its input config. This supports specification of leadtime-specific values. For example, the key-value pair

  .. code-block:: yaml

     suffix: f{{ '%03d' % (leadtime.total_seconds() / 3600) }}

  would be rendered as

  .. code-block:: yaml

     suffix: f018

  for leadtime 18.
