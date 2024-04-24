# pylint: disable=missing-function-docstring,protected-access,redefined-outer-name

# import datetime as dt
# from pathlib import Path
# from unittest.mock import patch

# from uwtools.api import chgres_cube


# def test_execute(tmp_path):
#     kwargs = {
#         "task": "foo",
#         "cycle": dt.datetime.now(),
#         "config": "config.yaml",
#         "batch": False,
#         "dry_run": True,
#         "graph_file": tmp_path / "g.dot",
#     }
#     with patch.object(chgres_cube, "execute", return_value=True) as execute:
#         assert chgres_cube.execute(**kwargs, stdin_ok=True) is True
#         _execute.assert_called_once_with(
#             **{**kwargs, "config": Path(kwargs["config"]), "driver_class": chgres_cube._Driver}
#         )
