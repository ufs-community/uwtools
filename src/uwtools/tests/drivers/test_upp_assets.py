from unittest.mock import patch

from uwtools.drivers.upp_assets import UPPAssets
from uwtools.tests.drivers import test_upp_common


def test_UPPAssets_control_file(upp_assets_driverobj):
    test_upp_common.control_file(upp_assets_driverobj)


def test_UPPAssets_driver_name(upp_assets_driverobj):
    assert upp_assets_driverobj.driver_name() == UPPAssets.driver_name() == "upp_assets"


def test_UPPAssets_files_copied(upp_assets_driverobj):
    test_upp_common.files_copied(upp_assets_driverobj)


def test_UPPAssets_files_linked(upp_assets_driverobj):
    test_upp_common.files_linked(upp_assets_driverobj)


def test_UPPAssets_namelist_file(upp_assets_driverobj, logged):
    test_upp_common.namelist_file(upp_assets_driverobj, logged)


def test_UPPAssets_namelist_file__fails_validation(upp_assets_driverobj, logged):
    test_upp_common.namelist_file__fails_validation(upp_assets_driverobj, logged)


def test_UPPAssets_namelist_file__missing_base_file(upp_assets_driverobj, logged):
    test_upp_common.namelist_file__missing_base_file(upp_assets_driverobj, logged)


def test_UPPAssets_output(upp_assets_driverobj, tmp_path):
    test_upp_common.output(upp_assets_driverobj, tmp_path)


def test_UPPAssets_output__fail(upp_assets_driverobj):
    test_upp_common.output__fail(upp_assets_driverobj)


def test_UPPAssets_provisioned_rundir(upp_assets_driverobj, ready_task):
    with patch.multiple(
        upp_assets_driverobj,
        files_copied=ready_task,
        files_hardlinked=ready_task,
        files_linked=ready_task,
        namelist_file=ready_task,
    ) as mocks:
        upp_assets_driverobj.provisioned_rundir()
    for m in mocks:
        mocks[m].assert_called_once_with()


def test_UPPAssets_taskname(upp_assets_driverobj):
    assert upp_assets_driverobj.taskname("foo") == "20240507 12:00:00 upp_assets foo"
