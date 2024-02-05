# pylint: disable=missing-function-docstring,protected-access

# import datetime as dt
# from unittest.mock import Mock, patch

# from uwtools.api import fv3

# def test_run():
#     SomeModel = Mock()
#     cycle = dt.datetime(2023, 11, 22, 12)
#     with patch.dict(forecast.CLASSES, {"foo": SomeModel}):
#         forecast.run(
#             model="foo",
#             cycle=cycle,
#             config_file="bar",
#             batch=True,
#             dry_run=False,
#         )
#     SomeModel.assert_called_once_with(
#         batch=True,
#         config_file="bar",
#         cycle=cycle,
#         dry_run=False,
#     )
#     SomeModel().run.assert_called_once_with()
