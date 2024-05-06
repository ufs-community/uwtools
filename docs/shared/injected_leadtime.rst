* This driver receives a ``leadtime`` argument, from which it computes a ``validtime`` Python ``datetime`` that it makes available to Jinja2 when realizing its input config. This supports specification of leadtime-specific values. For example, the values

  .. code-block:: yaml

     validstr: "{{ validtime.strftime('%Y-%m-%d %H:%M') }}"
     suffix: f{{ '%03d' % ((validtime - cycle).total_seconds() // 3600) }}

  would be rendered as

  .. code-block:: yaml

     validstr: 2024-02-12 18:00
     suffix: f018

  for cycle ``2024-02-12T18`` and leadtime ``18``.
