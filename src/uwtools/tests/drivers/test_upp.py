"""
UPP driver tests.
"""

from unittest.mock import patch

from uwtools.drivers.upp import UPP
from uwtools.tests.drivers import test_upp_common

# Tests


def test_UPP_control_file(upp_driverobj):
    test_upp_common.control_file(upp_driverobj)


def test_UPP_driver_name(upp_driverobj):
    assert upp_driverobj.driver_name() == UPP.driver_name() == "upp"


def test_UPP_files_copied(upp_driverobj):
    test_upp_common.files_copied(upp_driverobj)


def test_UPP_files_linked(upp_driverobj):
    test_upp_common.files_linked(upp_driverobj)


def test_UPP_namelist_file(upp_driverobj, logged):
    test_upp_common.namelist_file(upp_driverobj, logged)


def test_UPP_namelist_file__fails_validation(upp_driverobj, logged):
    test_upp_common.namelist_file__fails_validation(upp_driverobj, logged)


def test_UPP_namelist_file__missing_base_file(upp_driverobj, logged):
    test_upp_common.namelist_file__missing_base_file(upp_driverobj, logged)


def test_UPP_output(upp_driverobj, tmp_path):
    test_upp_common.output(upp_driverobj, tmp_path)


def test_UPP_output__fail(upp_driverobj):
    test_upp_common.output__fail(upp_driverobj)


def test_UPP_provisioned_rundir(upp_driverobj, ready_task):
    with patch.multiple(
        upp_driverobj,
        control_file=ready_task,
        files_copied=ready_task,
        files_hardlinked=ready_task,
        files_linked=ready_task,
        namelist_file=ready_task,
        runscript=ready_task,
    ):
        assert upp_driverobj.provisioned_rundir().ready


def test_UPP_taskname(upp_driverobj):
    assert upp_driverobj.taskname("foo") == "20240507 12:00:00 upp foo"


def test_UPP__runcmd(upp_driverobj):
    assert upp_driverobj._runcmd == "%s < itag" % upp_driverobj.config["execution"]["executable"]
