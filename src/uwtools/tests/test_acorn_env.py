"""
Acorn (WCOSS2 test environment) smoke tests.

Run these on Acorn after loading the workflow environment:

    module load intel
    module load ve/uwtools/0.1
    module load wgrib2/2.0.8

Then run using the PYTHONPATH workaround (pytest is not yet in ve/uwtools/0.1):

    PYTHONPATH=/apps/prod/ve/intel/19.1.3.304/python/3.12.0/mag/7.0/lib/python3.12/site-packages:/apps/prod/ve/intel/19.1.3.304/python/3.12.0/uwtools/0.1/lib/python3.12/site-packages \\
        python3 -m pytest src/uwtools/tests/test_acorn_env.py -v

NOTE: The PYTHONPATH workaround is needed because pytest is not installed in
ve/uwtools/0.1. It borrows pytest from the mag/7.0 VE while keeping the
uwtools/0.1 packages (iotaa, uwtools, etc.) active. Bongi has been asked to
add pytest to ve/uwtools/0.1 to eliminate this workaround.

These tests verify that the venv, uwtools version, and key dependencies
are functional before attempting a live workflow run on Acorn/WCOSS2.

===== VERSION TRACKING =====

uwtools versions:
  - Approved on WCOSS2 (in progress): 2.16.0      <- what this test suite targets
  - Required by uw-aigfs environment.yml (current): 2.18.*  <- must follow 2.16.0
  - Ecflow tool added to uw CLI: 2.17.0
  RISK: cli.py in v2.17+ eagerly imports uwtools.api.ecflow, which in turn does
  a hard top-level `from ecflow import ...`. On WCOSS2, ecflow is built against
  Python 3.8.6, so this import will fail from a Python 3.12+ venv — making the
  `uw` CLI entirely non-functional. v2.16.0 does NOT have this problem.
  ACTION: Before requesting 2.17+ approval, raise this with uw-tools team.
  See test_ecflow_cli_import_blocker_v217plus() for the regression check.

Python versions:
  - System Python on WCOSS2: 3.8.6  (DO NOT USE — ecflow is compiled against this)
  - Venv actual version (confirmed 2026-07-27): Python 3.12.0
    Source: /apps/prod/ve/intel/19.1.3.304/python/3.12.0/uwtools/0.1/bin/python3
  - uw-aigfs environment.yml: 3.14.*  (aspirational — reconcile with WCOSS2 avail)

ecflow versions:
  - WCOSS2 system ecflow: 5.6.x  (Python 3.8.6 bindings)
  - uwtools ecflow_tool requires: 5.15.x
  RESOLUTION (Phase 2 Task 2): Pre-generate suite .def on Ursa (ecflow 5.15.x) and
  commit it. On WCOSS2 use `ecflow_client --load` directly — bypassing uw ecflow realize.
  The ecflow Python bindings are NOT needed in the runtime venv for the NRT demo.

wgrib2 versions:
  - wgrib2/3.1.1: module exists but spack install is EMPTY — binary not found on disk.
    Path registered: /apps/spack/wgrib2/3.1.1/intel/19.1.3.304/.../bin (does not exist)
  - wgrib2/2.0.8: WORKING — binary at /apps/ops/prod/libs/intel/19.1.3.304/wgrib2/2.0.8/bin/wgrib2
    USE THIS VERSION until 3.1.1 is fixed by WCOSS2 admins.

===== KNOWN ISSUES =====

  1. ecflow/Python version mismatch: WCOSS2 ecflow 5.6.x built for Python 3.8.6;
     cannot be imported from a Python 3.12 venv. Not a blocker for v2.16.0 (no
     ecflow in CLI) but WILL block v2.17+ if not resolved first.

  2. graphcast pip install: WCOSS2 may lack outbound internet. If so, pre-clone
     noaa-emc/graphcast at commit aea0678c and install from a local path.

  3. aigfs_base.yaml key mismatch: parm/wflow/aigfs_base.yaml uses user.aigfs_home
     but ush/default_config.yaml (and wcoss_config.yaml) defines user.aigfs_app.
     This will cause a rendering failure regardless of platform. Needs a PR to
     uw-aigfs to fix the key name in aigfs_base.yaml.

  4. load_wflow_modules.sh: still hardcodes `conda activate aigfs`. Needs to be
     replaced with `module load wflow_wcoss` for WCOSS2 (Phase 2 Task 3).

  5. numpy/netCDF4 binary compatibility warning: test_netcdf4_import emits:
     RuntimeWarning: numpy.ndarray size changed, may indicate binary incompatibility.
     Expected 16 from C header, got 96 from PyObject
     Not a test failure, but flagged for Bongi — may indicate netCDF4 was compiled
     against a different numpy than what is in the VE.

  6. pytest not in ve/uwtools/0.1: must use PYTHONPATH workaround to borrow pytest
     from mag/7.0 VE. Bongi has been asked to add pytest to ve/uwtools/0.1.

  7. wgrib2/3.1.1 spack install is empty: use wgrib2/2.0.8 until fixed by WCOSS2 admins.

===== SMOKE TEST RESULTS — 2026-07-27 =====

  Environment:
    Node:          alogin01 (Acorn / WCOSS2)
    Modules:       intel, ve/uwtools/0.1, wgrib2/2.0.8
    Python:        3.12.0 (/apps/prod/ve/intel/19.1.3.304/python/3.12.0/uwtools/0.1/bin/python3)
    uwtools:       2.16.0 build 0
    pytest:        9.0.3 (borrowed from mag/7.0 VE via PYTHONPATH workaround)

  Results:
    PASSED  (12): test_python_version, test_uwtools_version, test_uwtools_schema_loading,
                  test_xarray_import, test_netcdf4_import, test_grib2io_import,
                  test_wgrib2_binary, test_pbs_scheduler_available, test_uw_cli_available,
                  test_uw_cli_version, test_uwtools_config_realize,
                  test_ecflow_cli_import_blocker_v217plus
    XFAIL   (2):  test_ecflow_import (expected — ecflow/Python 3.8.6 mismatch)
                  test_graphcast_import (expected — graphcast not yet installed)
    FAILED  (0):  none

  Warnings:
    - test_netcdf4_import: RuntimeWarning: numpy.ndarray size changed, may indicate
      binary incompatibility. Expected 16 from C header, got 96 from PyObject.
      Not a failure. Flagged for Bongi (see Known Issue 5).

  Outstanding requests to Bongi (GDIT):
    - Add to ve/uwtools/0.1: pytest, xarray (2026.4.*), netCDF4 (1.7.*), grib2io (2.7.*)
    - Fix or confirm wgrib2/3.1.1 spack install (currently empty); confirm 2.0.8 is OK
    - Confirm whether numpy/netCDF4 binary compatibility warning is expected in this VE

===== TODO: AFTER v2.16.0 APPROVAL =====

  [x] Run: python -m pytest src/uwtools/tests/test_acorn_env.py -v  (done 2026-07-27)
  [x] Record actual Python version available in the loaded venv  (Python 3.12.0)
  [x] Verify test_ecflow_import is correctly xfail (not unexpectedly passing)  (confirmed)
  [x] Confirm qsub is on PATH (test_pbs_scheduler_available)  (confirmed: /opt/pbs/bin/qsub)
  [x] Confirm wgrib2 is on PATH after module load (test_wgrib2_binary)  (confirmed: wgrib2/2.0.8)
  [x] Confirm `uw` is on PATH from the venv (test_uw_cli_available)  (confirmed)
  [x] Run test_uwtools_config_realize to confirm Jinja2 rendering works  (PASSED)
  [ ] Attempt graphcast install; update test_graphcast_import accordingly
  [ ] Begin v2.18.* approval process (uw-aigfs now requires 2.18.*, not 2.16.0)
  [ ] Build ush/wcoss_config.yaml (fork default_config.yaml with WCOSS2 paths)
  [ ] Build modulefiles/wflow_wcoss (Lmod/TCL; no conda; no ecflow in venv)
  [ ] Fix load_wflow_modules.sh: replace conda lines with `module load wflow_$1`
  [ ] Pre-generate suite .def on Ursa: `uw ecflow realize -c ush/wcoss_config.yaml`
  [ ] Commit rendered wcoss_suite.def; use `ecflow_client --load` on WCOSS2
  [ ] Confirm /lfs/h1/ops/prod/com/gfs/... path and data retention window
  [ ] Fix user.aigfs_home → user.aigfs_app in uw-aigfs parm/wflow/aigfs_base.yaml
  [ ] Raise v2.17+ ecflow CLI blocker with uw-tools team before upgrading
"""

import importlib.metadata
import shutil
import subprocess
import sys

import pytest


def test_python_version():
    """Python 3.12+ must be active — not the system Python 3.8.6 on WCOSS2."""
    major, minor = sys.version_info.major, sys.version_info.minor
    assert (major, minor) >= (3, 12), (
        f"Expected Python 3.12+, got {major}.{minor}. "
        "Check that wflow_wcoss venv is loaded, not system Python."
    )


def test_uwtools_version():
    """uwtools must be pinned to 2.16.0 in the active venv."""
    version = importlib.metadata.version("uwtools")
    assert version == "2.16.0", (
        f"Expected uwtools 2.16.0 but found {version}. "
        "Check that the correct venv is active."
    )


def test_uwtools_schema_loading():
    """Core uwtools API must load and return a valid schema dict."""
    import uwtools.api.ww3 as ww3

    schema_dict = ww3.schema()
    assert isinstance(schema_dict, dict), (
        "ww3.schema() did not return a dict — uwtools API may be broken."
    )


@pytest.mark.xfail(
    strict=False,
    reason=(
        "WCOSS2 ecflow 5.6.x is compiled against Python 3.8.6; "
        "import will fail from a Python 3.12+ venv. "
        "This is expected and NOT a blocker for v2.16.0 (no ecflow in CLI). "
        "Resolution: pre-generate suite .def on Ursa and use ecflow_client --load on WCOSS2."
    ),
)
def test_ecflow_import():
    """
    Check whether ecflow can be imported from within the uwtools venv.

    Expected to FAIL: WCOSS2 ecflow (5.6.x) is compiled against Python 3.8.6
    but the aigfs venv uses Python 3.12+. The fix is to pre-generate the ecflow
    suite definition file on Ursa (which has ecflow 5.15.x) and load it on
    WCOSS2 with `ecflow_client --load` directly — skipping `uw ecflow realize`
    at runtime entirely.

    If this unexpectedly passes, record the ecflow version for tracking.
    """
    import ecflow  # noqa: PLC0415

    version = getattr(ecflow, "__version__", "unknown")
    print(f"\necflow imported successfully — version: {version}")


# ─── Runtime Dependencies ────────────────────────────────────────────────────


def test_xarray_import():
    """xarray must be importable from the active venv (required by uw-aigfs drivers)."""
    import xarray as xr  # noqa: PLC0415

    assert xr.__version__, "xarray imported but __version__ is empty."


def test_netcdf4_import():
    """netCDF4 must be importable (required by generate_ics.py for IC file generation)."""
    import netCDF4 as nc  # noqa: PLC0415

    assert nc.__version__, "netCDF4 imported but __version__ is empty."


def test_grib2io_import():
    """grib2io must be importable (required for GRIB2 output handling in uw-aigfs)."""
    import grib2io  # noqa: PLC0415

    assert grib2io.__version__, "grib2io imported but __version__ is empty."


@pytest.mark.xfail(
    strict=False,
    reason=(
        "graphcast may not yet be installed. "
        "If WCOSS2 blocks outbound internet, pre-clone noaa-emc/graphcast at "
        "commit aea0678c and install from local path: "
        "pip install /path/to/local/graphcast"
    ),
)
def test_graphcast_import():
    """
    graphcast must be importable once the pinned-commit venv install is complete.

    Install command (with outbound internet):
        pip install git+https://github.com/noaa-emc/graphcast@aea0678cfbd7...
    Without outbound internet (WCOSS2 likely case):
        git clone https://github.com/noaa-emc/graphcast && cd graphcast
        git checkout aea0678cfbd7e866e4a1d364b456861d0a03954b
        pip install /path/to/graphcast
    """
    import graphcast  # noqa: PLC0415

    assert graphcast is not None


# ─── System Binaries ─────────────────────────────────────────────────────────


def test_wgrib2_binary():
    """
    wgrib2 must be on PATH — loaded via module load wgrib2 inside wflow_wcoss.

    wgrib2 is called directly by uw-aigfs post scripts and by generate_ics.py
    for GRIB2 variable extraction.

    NOTE: Use wgrib2/2.0.8 — wgrib2/3.1.1 spack install is currently empty on Acorn.
    """
    wgrib2_path = shutil.which("wgrib2")
    assert wgrib2_path is not None, (
        "wgrib2 not found on PATH. "
        "Check that the wflow_wcoss modulefile includes 'module load wgrib2'. "
        "Use wgrib2/2.0.8 — wgrib2/3.1.1 spack install is currently empty on Acorn."
    )


def test_pbs_scheduler_available():
    """
    qsub must be on PATH — WCOSS2 uses PBS Pro, not SLURM.

    Also confirms that uw-aigfs wcoss_config.yaml must set platform.scheduler: pbs
    (not slurm). Verify the exact scheduler string uwtools expects by checking
    uwtools/scheduler.py or running `uw config realize` with a test config.
    """
    qsub_path = shutil.which("qsub")
    assert qsub_path is not None, (
        "qsub not found on PATH. "
        "Verify PBS Pro is available on this Acorn node. "
        "Also confirm the scheduler string uwtools expects for PBS — check "
        "uwtools/scheduler.py for the registered scheduler identifiers."
    )


# ─── uwtools CLI ─────────────────────────────────────────────────────────────


def test_uw_cli_available():
    """
    The `uw` CLI entrypoint must be on PATH from the active venv.

    If this fails, check that the aigfs venv bin/ directory is first on PATH
    and that `pip install uwtools==2.16.0` succeeded without errors.
    """
    uw_path = shutil.which("uw")
    assert uw_path is not None, (
        "'uw' command not found on PATH. "
        "Check that the uwtools venv is active: "
        "source /path/to/aigfs-venv/bin/activate"
    )


def test_uw_cli_version():
    """
    `uw --version` must launch without errors and report 2.16.0.

    In v2.16.0 the CLI does NOT import ecflow, so this should work even though
    ecflow is not importable from the venv. If this fails with an ImportError for
    ecflow, the wrong uwtools version is installed — check with `pip show uwtools`.
    """
    result = subprocess.run(
        ["uw", "--version"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, (
        f"'uw --version' exited with code {result.returncode}.\n"
        f"stdout: {result.stdout}\nstderr: {result.stderr}\n"
        "If the error mentions 'ecflow', the wrong uwtools version is installed."
    )
    assert "2.16.0" in result.stdout or "2.16.0" in result.stderr, (
        f"Expected '2.16.0' in output, got stdout={result.stdout!r} "
        f"stderr={result.stderr!r}"
    )


# ─── uwtools Config Rendering ────────────────────────────────────────────────


def test_uwtools_config_realize():
    """
    uwtools config realize must correctly render Jinja2 cross-references in YAML.

    This exercises the same rendering path used by all uw-aigfs driver calls
    (generate_ics.py, run_graphcast.py) and by uw ecflow realize when building
    the pre-generated suite definition on Ursa.
    """
    import uwtools.api.config as uwconfig  # noqa: PLC0415

    input_cfg = {
        "user": {"platform": "wcoss2", "experiment_dir": "/some/exp"},
        "platform": {"scheduler": "pbs", "account": "MYACCT"},
        "rendered": {
            "sched": "{{ platform.scheduler }}",
            "plat": "{{ user.platform }}",
            "acct": "{{ platform.account }}",
        },
    }
    result = uwconfig.realize_to_dict(input_config=input_cfg)
    assert result["rendered"]["sched"] == "pbs", (
        f"Jinja2 rendering failed for scheduler: got {result['rendered']['sched']!r}"
    )
    assert result["rendered"]["plat"] == "wcoss2", (
        f"Jinja2 rendering failed for platform: got {result['rendered']['plat']!r}"
    )
    assert result["rendered"]["acct"] == "MYACCT", (
        f"Jinja2 rendering failed for account: got {result['rendered']['acct']!r}"
    )


# ─── ecflow Compatibility (v2.17+ Regression) ────────────────────────────────


def test_ecflow_cli_import_blocker_v217plus():
    """
    Confirm that importing uwtools core API modules does NOT pull in ecflow.

    In uwtools v2.17+, cli.py does `import uwtools.api.ecflow` at the top level,
    and uwtools/ecflow.py does `from ecflow import Defs, Suite, ...` at the top
    level. On WCOSS2, ecflow is compiled against Python 3.8.6 and cannot be
    imported from a Python 3.12+ venv — so the `uw` CLI will fail entirely.

    v2.16.0 does NOT have this problem (ecflow_tool was added in 2.17.0).

    This test confirms that importing the config, fs, and execute API modules
    (the ones uw-aigfs actually calls) does NOT trigger an ecflow import. If it
    does, raise with the uw-tools team immediately before requesting 2.17+ approval.
    """
    # Remove any cached ecflow entries to ensure a clean check
    for key in list(sys.modules.keys()):
        if "ecflow" in key:
            del sys.modules[key]

    safe_modules = [
        "uwtools.api.config",
        "uwtools.api.fs",
        "uwtools.api.execute",
    ]
    for mod_name in safe_modules:
        __import__(mod_name)
        ecflow_leaked = any("ecflow" in k for k in sys.modules)
        assert not ecflow_leaked, (
            f"Importing '{mod_name}' pulled in ecflow. "
            "This means uwtools eagerly imports ecflow at module load time. "
            "On WCOSS2 this will make ALL uwtools calls fail — not just ecflow_tool. "
            "Raise with uw-tools team before requesting 2.17+ WCOSS2 approval."
        )
