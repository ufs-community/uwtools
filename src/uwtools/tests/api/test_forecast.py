# pylint: disable=missing-function-docstring,protected-access

import datetime as dt
from unittest.mock import Mock, patch

from uwtools.api import forecast


def test_run():
    SomeModel = Mock()
    cycle = dt.datetime(2023, 11, 22, 12)
    with patch.dict(forecast._CLASSES, {"foo": SomeModel}):
        forecast.run(
            model="foo",
            cycle=cycle,
            config_file="bar",
            batch_script="baz",
            dry_run=False,
        )
    SomeModel.assert_called_once_with(
        batch_script="baz",
        config_file="bar",
        cycle=cycle,
        dry_run=False,
    )
    SomeModel().run.assert_called_once_with()
