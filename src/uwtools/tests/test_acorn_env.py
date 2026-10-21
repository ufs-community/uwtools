"""
Acorn / Cactus (WCOSS2 test environment) smoke tests.

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
add pytest to ve/uwtools/0.1 to eliminate this workaround. (As of 2026-08-06
the module-file contamination guard does NOT block this borrow — it still works.)

On Cactus, the GDIT-managed, security-patched VE is loaded instead via:

    module load intel/19.1.3.304
    module load ve/uwtools/2.16

which resolves to uwtools 2.16.3 (not 2.16.0 — see VERSION TRACKING below).

These tests verify that the venv, uwtools version, and key dependencies
are functional before attempting a live workflow run on Acorn/Cactus/Dogwood/WCOSS2.

===== VERSION TRACKING =====

uwtools versions:
  - Approved on WCOSS2 (in progress): 2.16.0 (Acorn) / 2.16.3 (Cactus, GDIT-patched)
      <- what this test suite targets; tests accept any 2.16.x patch release
  - Required by uw-aigfs environment.yml (current): 2.18.*  <- must follow 2.16.x
  - Ecflow tool added to uw CLI: 2.17.0
  RISK: cli.py in v2.17+ eagerly imports uwtools.api.ecflow, which in turn does
  a hard top-level `from ecflow import ...`. On WCOSS2, ecflow is built against
  Python 3.8.6, so this import will fail from a Python 3.12+ venv — making the
  `uw` CLI entirely non-functional. v2.16.x does NOT have this problem.
  ACTION: Before requesting 2.17+ approval, raise this with uw-tools team.
  See test_ecflow_cli_import_blocker_v217plus() for the regression check.

Python versions:
  - System Python on WCOSS2: 3.8.6  (DO NOT USE — ecflow is compiled against this)
  - Venv actual version (confirmed 2026-07-27, re-confirmed 2026-08-06, confirmed
    on Cactus 2026-10-20): Python 3.12.0
    Source (Acorn): /apps/prod/ve/intel/19.1.3.304/python/3.12.0/uwtools/0.1/bin/python3
    Source (Cactus): /apps/prod/ve/intel/19.1.3.304/python/3.12.0/uwtools/2.16/bin/python3
  - uw-aigfs environment.yml: 3.14.*  (aspirational — reconcile with WCOSS2 avail)

ecflow versions:
  - WCOSS2 system ecflow: 5.6.x  (Python 3.8.6 bindings)
  - uwtools ecflow_tool requires: 5.15.x
  RESOLUTION (Phase 2 Task 2): Pre-generate suite .def on Ursa (ecflow 5.15.x) and
  commit it. On WCOSS2 use `ecflow_client --load` directly — bypassing uw ecflow realize.
  The ecflow Python bindings are NOT needed in the runtime venv for the NRT demo.
  NOTE (2026-08-06): The VE now loads the ecflow/5.6.0.13 module at the shell level,
  but `import ecflow` from the VE's Python 3.12 still fails (ABI mismatch) — so
  test_ecflow_import remains XFAIL, as expected. Continued evidence that the 2.17+
  eager-import problem is real and unresolved. Still true on the Cactus 2.16.3 VE.

wgrib2 versions:
  - wgrib2/3.1.1: CONFIRMED a stale leftover stub (GDIT/bongi, 2026-08-04) from prior
    experimentation; never officially installed. To be removed by admins.
  - wgrib2/2.0.8: WORKING and OFFICIAL — binary at
    /apps/ops/prod/libs/intel/19.1.3.304/wgrib2/2.0.8/bin/wgrib2
    Also exists on Cactus/Dogwood, so it carries forward. USE THIS VERSION.

===== KNOWN ISSUES =====

  1. ecflow/Python version mismatch: WCOSS2 ecflow 5.6.x built for Python 3.8.6;
     cannot be imported from a Python 3.12 venv. Not a blocker for v2.16.x (no
     ecflow in CLI) but WILL block v2.17+ if not resolved first.

  2. graphcast: not installed in ve/uwtools/0.1 or ve/uwtools/2.16 (and not
     expected to be — graphcast lives in the ops venv aigfs.v1.1.0/venv). Acorn
     HAS outbound internet (confirmed 2026-07-27), so a direct pip install from
     noaa-emc/graphcast at commit aea0678c is possible if ever needed.
     test_graphcast_import stays XFAIL.
     UPDATE (2026-10-20): Based on the completed NRT runs of AIGFS on
     Cactus/Dogwood, the workflow only needs to point to pre-staged GraphCast
     model weights — it does not require the graphcast Python package to be
     importable from the uwtools VE itself. This further de-risks the XFAIL
     status of this test; it is not expected to become a real blocker.

  3. aigfs_base.yaml key mismatch: parm/wflow/aigfs_base.yaml uses user.aigfs_home
     but ush/default_config.yaml (and wcoss_config.yaml) defines user.aigfs_app.
     This will cause a rendering failure regardless of platform. Needs a PR to
     uw-aigfs to fix the key name in aigfs_base.yaml.

  4. load_wflow_modules.sh: still hardcodes `conda activate aigfs`. Needs to be
     replaced with `module load wflow_wcoss` for WCOSS2 (Phase 2 Task 3).

  5. numpy/netCDF4 binary compatibility warning: test_netcdf4_import emits:
     RuntimeWarning: numpy.ndarray size changed, may indicate binary incompatibility.
     Expected 16 from C header, got 96 from PyObject
     STILL PRESENT as of 2026-08-06 with the NATIVE VE packages (numpy 2.5.1,
     netCDF4 1.7.4). This is a build-time numpy C-ABI skew — netCDF4 was compiled
     against a different numpy than the VE ships. Not a test failure (netCDF4 imports
     and passes). It is NOT related to the OS-transition module-load errors. Fix:
     GDIT rebuild netCDF4 (and cftime) against the VE's numpy 2.5.1. Flagged for Bongi.

  6. pytest not in ve/uwtools/0.1: must use PYTHONPATH workaround to borrow pytest
     from mag/7.0 VE. George (GDIT) approved adding pytest to the uwtools ticket on
     2026-07-28, but it was not present in the 2026-08-04 build. Still borrowed as of
     2026-08-06. Awaiting inclusion in the next VE rebuild.

  7. wgrib2/3.1.1: CONFIRMED a stale stub by GDIT (2026-08-04), never officially
     installed. Use wgrib2/2.0.8 (official; also on Cactus/Dogwood).

  8. `uw fs` link/copy CLI config shape (2.16.0): the standalone `uw fs link` /
     `uw fs copy` commands expect a FLAT top-level `destination: source` map, with
     `--target-dir` supplying the root for relative destinations. They do NOT accept
     a top-level `link:` / `copy:` block, nor a `config:` wrapper — both raise
     "is not of type 'fs_src'". (The `link:` / `copy:` block form is only valid
     INSIDE a driver config such as `files_to_hardlink:`, which is a different code
     path.) Documented here so it doesn't have to be re-derived for uw-aigfs staging.

  9. uwtools patch-version drift between environments: Acorn validated 2.16.0;
     GDIT's Cactus VE (ve/uwtools/2.16) ships 2.16.3 (security-patched). Treat the
     2.16.x line as the approval unit rather than a single exact patch build, since
     GDIT may re-patch within a minor version for security reasons without that
     being a meaningful functional change. Confirmed working on Cactus 2026-10-20.

===== DRIVER AUTHORING NOTES for uwtools 2.16.0 (from the uw execute test) =====

  Deriving a minimal working custom driver on Acorn surfaced the exact 2.16.0 /
  iotaa contract. These apply directly when adapting the uw-aigfs drivers
  (generate_ics.py, run_graphcast.py):

  - A driver subclassing DriverCycleBased MUST implement the abstract method
    `provisioned_rundir`, decorated with iotaa's `@collection` (NOT `@tasks` —
    this iotaa build has no `tasks` export). Missing it -> TypeError "Can't
    instantiate abstract class ... without an implementation for 'provisioned_rundir'".

  - Every driver MUST ship a JSON schema next to its module, named
    `<driver_name>.jsonschema` (auto-resolved from driver_name()). Missing it ->
    FileNotFoundError on `<module_dir>/<driver_name>.jsonschema`. This is why the
    upstream drivers ship generate_ics.jsonschema / run_graphcast.jsonschema.

  - iotaa asset construction in this build: use the `Asset` CLASS, called
    positionally as `Asset(ref, ready)` where `ready` is a zero-arg callable
    returning bool. The lowercase `iotaa.asset` is NOT the builder (it takes a
    `Node`). `iotaa` exports (2.16.0 VE): Asset, Node, asset, collection, external,
    graph, log, logcfg, main, ready, ref, req, task, tasknames.

  - `@task` yield order that works: yield "<name>"; yield Asset(path, path.is_file);
    yield <requirements or None>; then the action code.

  - `uw execute` validates BOTH the driver's own schema AND an internal `platform`
    schema before running the requested task.

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

  NOTE: On this run xarray/netCDF4/grib2io passed only because the pytest PYTHONPATH
  workaround also pulled those packages in from the mag/7.0 VE — they were NOT yet
  native to ve/uwtools/0.1. (Resolved on 2026-08-06 — see below.)

  Warnings:
    - test_netcdf4_import: RuntimeWarning: numpy.ndarray size changed, may indicate
      binary incompatibility. Expected 16 from C header, got 96 from PyObject.
      Not a failure. Flagged for Bongi (see Known Issue 5).

  Outstanding requests to Bongi (GDIT):
    - Add to ve/uwtools/0.1: pytest, xarray (2026.4.*), netCDF4 (1.7.*), grib2io (2.7.*)
    - Fix or confirm wgrib2/3.1.1 spack install (currently empty); confirm 2.0.8 is OK
    - Confirm whether numpy/netCDF4 binary compatibility warning is expected in this VE

===== SMOKE TEST RESULTS — 2026-08-06 (native packages, post-OS-transition) =====

  Context:
    - GDIT (bongi) rebuilt ve/uwtools/0.1 (build report 2026-08-04) adding the
      requested Python libraries NATIVELY: xarray 2026.4.0, netCDF4 1.7.4,
      grib2io 2.5.4, pyproj 3.7.1 (+ numpy 2.5.1, pandas, cftime, etc.).
      Versions were rolled back from the exact requested pins due to compile-time
      incompatibilities; the rolled-back set matches the NOAA software ecosystem
      (grib2io 2.5.4 also matches the ops aigfs.v1.1.0/venv). Rollback accepted.
    - Acorn was in an OS-rollout transition; an earlier load failed with missing
      MPI/IO dependency modules (hdf5-D/netcdf-D/pnetcdf-D/pio-D). GDIT (George)
      identified this as transient transition-state churn; a clean retry on
      2026-08-06 loaded the VE with NO errors.
    - FIRST run where xarray/netCDF4/grib2io are confirmed NATIVE to the VE
      (imported successfully with NO PYTHONPATH set, before pytest ran).

  Environment:
    Node:          alogin01 (Acorn / WCOSS2)
    Modules:       intel, ve/uwtools/0.1, wgrib2/2.0.8
    Python:        3.12.0 (/apps/prod/ve/intel/19.1.3.304/python/3.12.0/uwtools/0.1/bin/python3)
    VIRTUAL_ENV:   /apps/prod/ve/intel/19.1.3.304/python/3.12.0/uwtools/0.1
    uwtools:       2.16.0 build 0
    Native pkgs:   xarray 2026.4.0, netCDF4 1.7.4, grib2io 2.5.4, numpy 2.5.1
    wgrib2:        2.0.8 (/apps/ops/prod/libs/intel/19.1.3.304/wgrib2/2.0.8/bin/wgrib2)
    pytest:        9.0.3 (still borrowed from mag/7.0 VE — not yet in the VE)

  Results:
    PASSED  (12): test_python_version, test_uwtools_version, test_uwtools_schema_loading,
                  test_xarray_import, test_netcdf4_import, test_grib2io_import,
                  test_wgrib2_binary, test_pbs_scheduler_available, test_uw_cli_available,
                  test_uw_cli_version, test_uwtools_config_realize,
                  test_ecflow_cli_import_blocker_v217plus
    XFAIL   (2):  test_ecflow_import (expected — ecflow/Python 3.8.6 ABI mismatch;
                  still XFAIL even though the VE now loads the ecflow module)
                  test_graphcast_import (expected — graphcast not in this VE by design)
    FAILED  (0):  none

  Warnings:
    - test_netcdf4_import: RuntimeWarning: numpy.ndarray size changed... Expected 16
      from C header, got 96 from PyObject. STILL PRESENT with native numpy 2.5.1 /
      netCDF4 1.7.4. Not a failure. See Known Issue 5.

  Deltas vs. 2026-07-27:
    - xarray/netCDF4/grib2io now pass NATIVELY (previously borrowed from mag/7.0).
    - wgrib2/3.1.1 resolved: confirmed a stale stub; 2.0.8 is the official version.
    - ecflow module now loads at shell level but import still fails (XFAIL) — good.

===== CLI FUNCTIONAL VALIDATION — 2026-08-18 (beyond the smoke suite) =====

  Ran the uwtools CLI primitives directly on Acorn (alogin01) with uwtools 2.16.0
  in ve/uwtools/0.1. These exercise the actual `uw` subcommands uw-aigfs relies on,
  which the in-process smoke tests above do not cover.

  uw config realize:
    - `uw config realize --input-file ush/wcoss_config.yaml --values-needed` -> clean
      (no unrendered keys/values); full render exits 0 with no leftover Jinja2.
    - Confirms 2.16.0 renders a REAL WCOSS2 config end-to-end, not just the synthetic
      test_uwtools_config_realize case.

  uw config validate:  PASS (positive + negative)
    - Real driver schema vs. the overlay: validator ran and correctly reported
      "'aigfs_ics' is a required property" — i.e. the top-level overlay is not a full
      driver config (expected mismatch, not a bug; proves validate executes).
    - mini_good.yaml (has platform.scheduler + account) -> "Schema validation
      succeeded for config".
    - mini_bad.yaml (missing account) -> "'account' is a required property", reported
      "at platform:" — correct location. Confirms validate catches errors precisely.

  uw fs makedirs:  PASS
    - Validated against internal schema, created /tmp/uw_fs_test/{a,b}, "Ready".

  uw fs link:  PASS
    - Flat map (linked.txt: <src>) + --target-dir /tmp/uw_fs_test -> symlink created,
      "File links: Ready".

  uw fs copy:  PASS
    - Flat map (copied.txt: <src>) + --target-dir /tmp/uw_fs_test -> real copy created
      (17 bytes, contents intact), "File copies: Ready".

  See Known Issue 8 for the exact `uw fs` link/copy config shape on 2.16.0.

  uw execute:  PASS  (minimal custom driver, run to completion)
    - Authored a minimal DriverCycleBased driver (/tmp/mydriver.py) with one @task
      (`greet`, writes hello.txt), the required `provisioned_rundir` @collection, a
      matching /tmp/mydriver.jsonschema, and a tiny config (mydriver: {rundir: ...}).
    - `uw execute --module /tmp/mydriver.py --classname MyDriver --task greet
       --config-file mydriver.yaml --cycle 2026-08-18T00` output:
         INFO Schema validation succeeded for mydriver config
         INFO Schema validation succeeded for platform config
         INFO greet: Executing
         INFO greet: Ready
      and /tmp/uw_exec_test/hello.txt was created with the expected contents.
    - Confirms the FULL execute path on 2.16.0: CLI dispatch -> module load ->
      class instantiation -> config + platform schema validation -> iotaa task graph
      resolution -> task execution -> asset ready. See DRIVER AUTHORING NOTES above.
    - NOTE: this proves the uw execute MACHINERY. Running a REAL uw-aigfs driver
      (generate_ics.py / run_graphcast.py) is still deferred to the actual workflow
      run — it needs graphcast installed, staged GFS input, and the v1.1 model
      weights on the machine (weights currently live on Dogwood, not Acorn).

  Net: 2.16.0 CLI primitives realize / validate / fs (makedirs, link, copy) / execute
  are ALL confirmed working on Acorn. Remaining execute work is a real-driver run,
  not a uwtools-primitive gap.

  Still outstanding to Bongi (GDIT):
    - Add pytest to ve/uwtools/0.1 (approved 2026-07-28; not in 2026-08-04 build).
    - numpy/netCDF4 binary-compatibility warning persists — rebuild netCDF4/cftime
      against the VE's numpy 2.5.1 to clear it.

===== CACTUS VE CONFIRMATION — 2026-10-20 =====

  Context:
    - Bongi (GDIT) reported ve/uwtools/2.16 installed on Cactus 10/16/2026 (install
      on Dogwood was planned for the same date; status to be confirmed separately).
    - This is a HIERARCHICAL module: it is hidden from `module avail` until one of
      its prerequisite compiler modules is loaded. Loading intel/19.1.3.304 (same
      compiler family as the Acorn VE) makes it visible and loadable.

  Confirmed load sequence (clogin, Cactus):
    module load intel/19.1.3.304
    module load ve/uwtools/2.16

  Environment:
    Node:        clogin05/clogin06 (Cactus)
    Python:      3.12.0 (/apps/prod/ve/intel/19.1.3.304/python/3.12.0/uwtools/2.16/bin/python3)
    uwtools:     2.16.3 (NOT 2.16.0 — GDIT security-patched build)
    VE packages (per `module spider`): f90nml 1.5.0, iotaa 1.6.0, jinja2 3.1.6,
      jsonschema 4.26.0, lxml 6.0.2, python-dateutil 2.9.0.post0, pyyaml 6.0.3,
      requests 2.33.0, xarray 2026.4.0, netcdf4 1.7.4, pyproj 3.7.1, numpy 2.4.1,
      grib2io 2.5.4, pytest 9.1.1, uwtools 2.16.3.
    graphcast: NOT present in this VE (by design — see Known Issue 2 update above).

  Action taken: relaxed test_uwtools_version and test_uw_cli_version to accept
  any 2.16.x patch release (was a strict == "2.16.0" check), since GDIT's security
  patching legitimately advances the patch version independent of uw-aigfs/uw-tools
  functional changes.

  Still outstanding:
    - Confirm Dogwood install status (planned 10/16; not yet directly confirmed here).
    - ecflow/Python ABI mismatch unresolved in 2.16.3, as expected; must be re-checked
      once GDIT bumps uwtools toward 2.20.*/2.21.* to satisfy uw-aigfs's 2.18+
      requirement and to pick up ecflow_tool — at which point the v2.17+ eager-import
      blocker (test_ecflow_cli_import_blocker_v217plus) becomes directly relevant and
      must be re-run against whatever version GDIT delivers.

===== CACTUS SMOKE TEST RESULTS — 2026-10-20 (GDIT VE ve/uwtools/2.16, uwtools 2.16.3) =====

  Environment:
    Node:        clogin07 (Cactus / WCOSS2)
    Modules:     intel/19.1.3.304, ve/uwtools/2.16
    Python:      3.12.0 (/apps/prod/ve/intel/19.1.3.304/python/3.12.0/uwtools/2.16/bin/python3)
    uwtools:     2.16.3

  Results:
    PASSED  (12), XFAIL (2), FAILED (0) — clean sweep, matching the Acorn 2.16.0 profile.
    XFAILs: test_ecflow_import (expected — ecflow/Python 3.8.6 ABI mismatch, unresolved
    in 2.16.3 as expected), test_graphcast_import (expected — graphcast package not
    present in this VE by design; only pre-staged model weights are needed).

  Confirms: the GDIT-patched 2.16.3 VE on Cactus behaves identically to the validated
  2.16.0 VE on Acorn for all primitives this suite covers.

===== TODO: AFTER v2.16.x APPROVAL =====

  [x] Run: python -m pytest src/uwtools/tests/test_acorn_env.py -v  (done 2026-07-27; re-run 2026-08-06)
  [x] Record actual Python version available in the loaded venv  (Python 3.12.0)
  [x] Verify test_ecflow_import is correctly xfail (not unexpectedly passing)  (confirmed 07-27 & 08-06)
  [x] Confirm qsub is on PATH (test_pbs_scheduler_available)  (confirmed: /opt/pbs/bin/qsub)
  [x] Confirm wgrib2 is on PATH after module load (test_wgrib2_binary)  (confirmed: wgrib2/2.0.8)
  [x] Confirm `uw` is on PATH from the venv (test_uw_cli_available)  (confirmed)
  [x] Run test_uwtools_config_realize to confirm Jinja2 rendering works  (PASSED)
  [x] Confirm xarray/netCDF4/grib2io are NATIVE to the VE (not borrowed)  (confirmed 2026-08-06)
  [x] Confirm wgrib2 version question with GDIT  (2.0.8 official; 3.1.1 stale stub)
  [x] Functional: uw config realize against a real WCOSS2 config on Acorn  (clean render 2026-08-18)
  [x] Functional: uw config validate (positive + negative) on Acorn  (PASS 2026-08-18)
  [x] Functional: uw fs makedirs / link / copy on Acorn  (all PASS 2026-08-18)
  [x] Functional: uw execute (minimal custom driver, run to completion) on Acorn  (PASS 2026-08-18)
  [x] Confirm GDIT VE (ve/uwtools/2.16) loads cleanly on Cactus  (confirmed 2026-10-20, uwtools 2.16.3)
  [x] Relax strict 2.16.0 version assertions to accept 2.16.x patch releases  (this change)
  [x] Run full smoke suite against the Cactus VE and record PASS/XFAIL counts  (12 passed, 2 xfailed, 0 failed — 2026-10-20)
  [ ] Confirm Dogwood install of ve/uwtools/2.16 (planned 10/16)
  [ ] Functional: uw execute a REAL uw-aigfs driver — deferred to the real run (needs
      GraphCast model weights staged + GFS input; graphcast package import NOT required)
  [ ] Get pytest added to ve/uwtools/0.1 on Acorn (already native in Cactus 2.16.3 VE)
  [ ] Begin v2.18.*/2.20.*/2.21.* approval process with GDIT (uw-aigfs requires 2.18.*)
  [ ] Build modulefiles/wflow_wcoss (Lmod/TCL; no conda; no ecflow in venv)
  [ ] Fix load_wflow_modules.sh: replace conda lines with `module load wflow_$1`
  [ ] Pre-generate suite .def on Ursa: `uw ecflow realize -c ush/wcoss_config.yaml`
  [ ] Commit rendered wcoss_suite.def; use `ecflow_client --load` on WCOSS2
  [ ] Confirm /lfs/h1/ops/prod/com/gfs/... path and data retention window
  [ ] Fix user.aigfs_home → user.aigfs_app in uw-aigfs parm/wflow/aigfs_base.yaml
  [ ] Raise v2.17+ ecflow CLI blocker with uw-tools team before upgrading past 2.16.x
"""

import importlib.metadata
import re
import shutil
import subprocess
import sys

import pytest


def test_python_version():
    """
    Python 3.12+ must be active — not the system Python 3.8.6 on WCOSS2.
    """
    major, minor = sys.version_info.major, sys.version_info.minor
    assert (major, minor) >= (3, 12), (
        f"Expected Python 3.12+, got {major}.{minor}. "
        "Check that wflow_wcoss venv is loaded, not system Python."
    )


def test_uwtools_version():
    """
    Uwtools must be pinned to the 2.16.x line in the active venv.

    Acorn's VE shipped 2.16.0; GDIT's Cactus VE (ve/uwtools/2.16) ships a security-patched 2.16.3.
    Both are valid instances of the approved 2.16 minor version, so accept any 2.16.x patch release
    here.
    """
    version = importlib.metadata.version("uwtools")
    assert re.match(r"^2\.16\.\d+$", version), (
        f"Expected uwtools 2.16.x but found {version}. Check that the correct venv is active."
    )


def test_uwtools_schema_loading():
    """
    Core uwtools API must load and return a valid schema dict.
    """
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
        "This is expected and NOT a blocker for v2.16.x (no ecflow in CLI). "
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
    """
    Xarray must be importable from the active venv (required by uw-aigfs drivers).
    """
    import xarray as xr  # noqa: PLC0415

    assert xr.__version__, "xarray imported but __version__ is empty."


def test_netcdf4_import():
    """
    NetCDF4 must be importable (required by generate_ics.py for IC file generation).
    """
    import netCDF4 as nc  # noqa: PLC0415

    assert nc.__version__, "netCDF4 imported but __version__ is empty."


def test_grib2io_import():
    """
    Grib2io must be importable (required for GRIB2 output handling in uw-aigfs).
    """
    import grib2io  # noqa: PLC0415

    assert grib2io.__version__, "grib2io imported but __version__ is empty."


@pytest.mark.xfail(
    strict=False,
    reason=(
        "graphcast may not yet be installed, and per completed NRT runs on "
        "Cactus/Dogwood, the workflow only needs pre-staged GraphCast model "
        "weights — not a graphcast Python package import in the uwtools VE. "
        "If WCOSS2 blocks outbound internet and a graphcast import is ever "
        "needed, pre-clone noaa-emc/graphcast at commit aea0678c and install "
        "from local path: pip install /path/to/local/graphcast"
    ),
)
def test_graphcast_import():
    """
    Graphcast may become importable if the pinned-commit venv install is completed.

    Install command (with outbound internet):
        pip install git+https://github.com/noaa-emc/graphcast@aea0678cfbd7...
    Without outbound internet (WCOSS2 likely case):
        git clone https://github.com/noaa-emc/graphcast && cd graphcast
        git checkout aea0678cfbd7e866e4a1d364b456861d0a03954b
        pip install /path/to/graphcast

    NOTE: confirmed via completed NRT runs that this import is not actually
    required for the workflow to function — only access to pre-staged model
    weights is needed. Retained as XFAIL rather than removed, for environment
    tracking purposes.
    """
    import graphcast  # noqa: PLC0415

    assert graphcast is not None


# ─── System Binaries ────────────────────────────────────────────────────────


def test_wgrib2_binary():
    """
    Wgrib2 must be on PATH — loaded via module load wgrib2 inside wflow_wcoss.

    wgrib2 is called directly by uw-aigfs post scripts and by generate_ics.py
    for GRIB2 variable extraction.

    NOTE: Use wgrib2/2.0.8 — wgrib2/3.1.1 is a stale stub (confirmed by GDIT 2026-08-04).
    """
    wgrib2_path = shutil.which("wgrib2")
    assert wgrib2_path is not None, (
        "wgrib2 not found on PATH. "
        "Check that the wflow_wcoss modulefile includes 'module load wgrib2'. "
        "Use wgrib2/2.0.8 — wgrib2/3.1.1 is a stale stub on Acorn."
    )


def test_pbs_scheduler_available():
    """
    Qsub must be on PATH — WCOSS2 uses PBS Pro, not SLURM.

    Also confirms that uw-aigfs wcoss_config.yaml must set platform.scheduler: pbs (not slurm).
    Verify the exact scheduler string uwtools expects by checking uwtools/scheduler.py or running
    `uw config realize` with a test config.
    """
    qsub_path = shutil.which("qsub")
    assert qsub_path is not None, (
        "qsub not found on PATH. "
        "Verify PBS Pro is available on this node. "
        "Also confirm the scheduler string uwtools expects for PBS — check "
        "uwtools/scheduler.py for the registered scheduler identifiers."
    )


# ─── uwtools CLI ─────────────────────────────────────────────────────────────


def test_uw_cli_available():
    """
    The `uw` CLI entrypoint must be on PATH from the active venv.

    If this fails, check that the aigfs venv bin/ directory is first on PATH and that `pip install
    uwtools==2.16.*` succeeded without errors.
    """
    uw_path = shutil.which("uw")
    assert uw_path is not None, (
        "'uw' command not found on PATH. "
        "Check that the uwtools venv is active: "
        "source /path/to/aigfs-venv/bin/activate"
    )


def test_uw_cli_version():
    """
    `uw --version` must launch without errors and report a 2.16.x version.

    In v2.16.x the CLI does NOT import ecflow, so this should work even though ecflow is not
    importable from the venv. If this fails with an ImportError for ecflow, the wrong uwtools
    version is installed — check with `pip show uwtools`.
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
    combined_output = result.stdout + result.stderr
    assert re.search(r"2\.16\.\d+", combined_output), (
        f"Expected a '2.16.x' version string in output, got stdout={result.stdout!r} "
        f"stderr={result.stderr!r}"
    )


# ─── uwtools Config Rendering ────────────────────────────────────────────────


def test_uwtools_config_realize():
    """
    Uwtools config realize must correctly render Jinja2 cross-references in YAML.

    This exercises the same rendering path used by all uw-aigfs driver calls (generate_ics.py,
    run_graphcast.py) and by uw ecflow realize when building the pre-generated suite definition on
    Ursa.
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

    v2.16.x does NOT have this problem (ecflow_tool was added in 2.17.0).

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
