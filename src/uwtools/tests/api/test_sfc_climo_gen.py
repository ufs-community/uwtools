# pylint: disable=missing-function-docstring,protected-access,redefined-outer-name

from pathlib import Path
from unittest.mock import patch

from uwtools.api import sfc_climo_gen


def test_execute(tmp_path):
    kwargs = {
        "task": "foo",
        "config": "config.yaml",
        "batch": False,
        "dry_run": True,
        "graph_file": tmp_path / "g.dot",
    }
    with patch.object(sfc_climo_gen, "_execute", return_value=True) as _execute:
        assert sfc_climo_gen.execute(**kwargs, stdin_ok=True) is True
        _execute.assert_called_once_with(
            **{**kwargs, "config": Path(kwargs["config"]), "driver_class": sfc_climo_gen._Driver}
        )
