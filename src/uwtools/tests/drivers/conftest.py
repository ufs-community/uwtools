import datetime as dt

from pytest import fixture

from uwtools.drivers.upp import UPP
from uwtools.drivers.upp_assets import UPPAssets


@fixture
def cycle(utc):
    return utc(2024, 5, 6, 12)


@fixture
def leadtime():
    return dt.timedelta(hours=24)


@fixture
def upp_config(tmp_path, upp_assets_config):
    config = {"upp": upp_assets_config["upp-assets"]}
    config["upp"]["execution"] = {
        "batchargs": {
            "cores": 1,
            "walltime": "00:01:00",
        },
        "executable": str(tmp_path / "upp.exe"),
    }
    return config


@fixture
def upp_assets_config(tmp_path):
    return {
        "upp-assets": {
            "control_file": "/path/to/postxconfig-NT.txt",
            "files_to_copy": {
                "foo": str(tmp_path / "foo"),
                "bar": str(tmp_path / "bar"),
            },
            "files_to_link": {
                "baz": str(tmp_path / "baz"),
                "qux": str(tmp_path / "qux"),
            },
            "namelist": {
                "base_file": str(tmp_path / "base.nml"),
                "update_values": {
                    "model_inputs": {
                        "grib": "grib2",
                    },
                    "nampgb": {
                        "kpo": 3,
                    },
                },
            },
            "rundir": str(tmp_path / "run"),
        },
        "platform": {
            "account": "me",
            "scheduler": "slurm",
        },
    }


@fixture
def upp_driverobj(upp_config, cycle, leadtime):
    return UPP(config=upp_config, cycle=cycle, leadtime=leadtime, batch=True)


@fixture
def upp_assets_driverobj(upp_assets_config, cycle, leadtime):
    return UPPAssets(config=upp_assets_config, cycle=cycle, leadtime=leadtime)
