# Acorn (WCOSS2) Testing Runbook

**Branch:** `acorn_testing`
**Goal:** Verify that uwtools v2.16.0 builds, installs, and operates correctly
on the Acorn WCOSS2 test environment before formal approval.

---

## What You Need vs. What the Tests Do

The pytest smoke tests in `src/uwtools/tests/test_acorn_env.py` **verify** the
environment — they do not build it. Think of them as a checklist that tells you
whether each prerequisite is in place. You need to:

1. Set up the venv (one-time, manual steps below)
2. Load the environment (each session)
3. Run the smoke tests (quick pass/fail on all prerequisites)
4. If smoke tests pass, run the functional validation commands (manual, below)

The tests will tell you exactly which step failed and why if something is wrong.

---

## Part 1: One-Time Setup (Do This First)

### 1.1 Check What Python Is Available

```bash
module avail python
```

Look for Python 3.12 or higher. Do **not** use the system default (3.8.6).
Record the exact module name — you'll need it in the modulefile.

```bash
# Load it and confirm:
module load python/3.XX.X
python3 --version
```

### 1.2 Check What Other System Modules Exist

```bash
module avail wgrib2
module avail netcdf4
module avail xarray
```

Anything available as a system module does not need to be pip-installed.
Record what you find — it affects the venv build and the wflow_wcoss modulefile.

### 1.3 Create the aigfs venv

```bash
module load python/3.XX.X          # use the version found in 1.1
python3 -m venv /path/to/aigfs-venv
source /path/to/aigfs-venv/bin/activate
```

Replace `/path/to/aigfs-venv` with a writable path under your WCOSS2 home or
scratch space (e.g. `$HOME/aigfs-venv` or `$DATAROOT/aigfs-venv`).

### 1.4 Install uwtools (no-deps first to avoid ecflow)

```bash
# Install uwtools without pulling in its full dependency tree yet.
# This avoids pip trying to resolve/install ecflow from PyPI.
pip install --no-deps uwtools==2.16.0

# Verify:
pip show uwtools
```

### 1.5 Install Remaining Runtime Dependencies

Install these individually so you can see which one fails if something goes wrong:

```bash
pip install xarray==2026.4.*
pip install netcdf4==1.7.*
pip install grib2io==2.7.*

# For any package already available as a system module (found in 1.2),
# skip the pip install and use PYTHONPATH to point at the system version instead:
# export PYTHONPATH=/path/to/system/module/site-packages:$PYTHONPATH
```

### 1.6 Install graphcast (may require local staging)

WCOSS2 may not have outbound internet. Try the direct install first:

```bash
pip install git+https://github.com/noaa-emc/graphcast@aea0678cfbd7e866e4a1d364b456861d0a03954b
```

If that fails with a network error, pre-stage the repo:

```bash
# On a system with internet access, clone and archive:
git clone https://github.com/noaa-emc/graphcast
cd graphcast
git checkout aea0678cfbd7e866e4a1d364b456861d0a03954b
# Copy/transfer the directory to WCOSS2, then:
pip install /path/to/graphcast
```

### 1.7 Create the wflow_wcoss Modulefile (Phase 2 Task 3)

This step is part of Phase 2 but you'll need at least a minimal version to
load the venv for testing. Create `uw-aigfs/modulefiles/wflow_wcoss`:

```tcl
#%Module1.0
# wflow_wcoss — loads the aigfs Python venv on WCOSS2

module load python/3.XX.X          # match what you used in 1.1
module load wgrib2                  # system wgrib2

# Activate the venv
prepend-path PATH /path/to/aigfs-venv/bin
prepend-path PYTHONPATH /path/to/aigfs-venv/lib/python3.XX/site-packages

# Do NOT load ecflow here — not needed in the runtime venv for the NRT demo
```

---

## Part 2: Each Session — Load the Environment

```bash
# From the uw-aigfs repo root:
module use $PWD/modulefiles
module load wflow_wcoss

# Verify you have the right Python (not 3.8.6):
python3 --version

# Verify uw is on PATH:
which uw
uw --version
```

If `uw --version` fails with an ImportError mentioning ecflow, the wrong
uwtools version is installed. Check with `pip show uwtools`.

---

## Part 3: Run the Smoke Tests

From the uwtools repo root with the venv active:

```bash
python3 -m pytest src/uwtools/tests/test_acorn_env.py -v
```

### What each test checks and what to do if it fails:

| Test | Checks | If it fails |
|---|---|---|
| `test_python_version` | Python ≥ 3.12 is active | System Python loaded instead of venv |
| `test_uwtools_version` | uwtools 2.16.0 is installed | Wrong version or pip install failed |
| `test_uwtools_schema_loading` | Core uwtools API loads without error | uwtools install is broken or corrupt |
| `test_ecflow_import` | ecflow importable (expected to FAIL — marked xfail) | If it passes, record the ecflow version |
| `test_xarray_import` | xarray is installed | `pip install xarray` in the venv |
| `test_netcdf4_import` | netCDF4 is installed | `pip install netcdf4` in the venv |
| `test_grib2io_import` | grib2io is installed | `pip install grib2io` in the venv |
| `test_graphcast_import` | graphcast is installed (expected to FAIL until installed — xfail) | See 1.6 above |
| `test_wgrib2_binary` | `wgrib2` is on PATH | Add `module load wgrib2` to wflow_wcoss |
| `test_pbs_scheduler_available` | `qsub` is on PATH | Confirm PBS is accessible on this node |
| `test_uw_cli_available` | `uw` command is on PATH | venv bin/ not on PATH; check module file |
| `test_uw_cli_version` | `uw --version` runs and reports 2.16.0 | Wrong uwtools version installed |
| `test_uwtools_config_realize` | Jinja2 YAML rendering works end-to-end | Core uwtools broken; check pip install |
| `test_ecflow_cli_import_blocker_v217plus` | Config/fs/execute APIs don't leak ecflow at import | Would only fail on v2.17+; safe on 2.16.0 |

### Interpreting results:

```
PASSED  — requirement met
FAILED  — requirement not met; fix before proceeding
xfail   — expected failure (ecflow, graphcast); not a blocker
xpass   — expected failure but it passed; note the version and update the test
```

**Target for passing Phase 2 gate:** all tests PASSED or xfail, with no unexpected FAILs.

---

## Part 4: Functional Validation (Beyond the Tests)

Once smoke tests pass, verify that uwtools actually does useful work on Acorn.
These are manual commands — they are not covered by the test file.

### 4.1 Config Realize with a Real Config File

```bash
# From the uw-aigfs repo:
uw config realize \
    --input-file ush/wcoss_config.yaml \
    --output-file /tmp/realized_config.yaml

# Then inspect:
cat /tmp/realized_config.yaml
# Verify that all {{ }} Jinja2 references are resolved (no bare {{ }} in output)
```

### 4.2 Validate the aigfs Config Against Its Schema

```bash
uw config validate \
    --schema-file parm/schema/aigfs_config.yaml \
    --input-file ush/wcoss_config.yaml
```

### 4.3 Verify `uw execute` Can Find the Driver

```bash
# Dry run only — just checks that uwtools can load the driver module
uw execute \
    --module drivers/generate_ics.py \
    --classname GenICS \
    --task run \
    --config ush/wcoss_config.yaml \
    --cycle 2025-10-21T00 \
    --key-path prep \
    --dry-run
```

This should print the resolved configuration without submitting any jobs.
If it fails with ImportError for graphcast, that's expected until graphcast
is installed (see 1.6 above).

### 4.4 Check GFS Data Path

```bash
# Confirm the operational GFS data path exists and is readable:
ls /lfs/h1/ops/prod/com/gfs/v16.*/gfs.YYYYMMDD/HH/atmos/

# Replace YYYYMMDD/HH with a recent archived date (within retention window).
# Confirm the pgrb2.0p25.f000 and pgrb2.0p25.f006 files are present.
```

Record the exact base path and update `user.gfs_data` in `ush/wcoss_config.yaml`.

### 4.5 Load ecflow and Check the Server (Separate from the Venv)

ecflow is NOT in the venv. Load it separately as a system module:

```bash
module load ecflow     # loads WCOSS2 system ecflow 5.6.x
ecflow_client --version
ecflow_client --ping --host <ecflow_server_host> --port <port>
```

Get the server hostname and port from WCOSS2 admin or the uw-aigfs team.

---

## Part 5: After v2.16.0 Passes — Next Steps

If all smoke tests and functional checks pass, the environment is ready for Phase 3.
Before that:

- [ ] Push test results to the `acorn_testing` branch (annotate which xfails changed)
- [ ] Begin v2.17.0 / v2.18.* approval request (uw-aigfs requires 2.18.*)
  - **Before submitting the 2.17+ request**, raise the lazy-import issue with the
    uw-tools team (see `acorn/ECFLOW_PYTHON_ISSUES.md`)
- [ ] Build `ush/wcoss_config.yaml` with confirmed WCOSS2 paths from step 4.4
- [ ] Pre-generate `parm/wflow/wcoss_suite.def` on Ursa using `uw ecflow realize`
- [ ] Fix `user.aigfs_home` → `user.aigfs_app` key mismatch in `parm/wflow/aigfs_base.yaml`
  (open a PR in uw-aigfs)

---

## Quick Reference

```bash
# Load environment (each session):
module use /path/to/uw-aigfs/modulefiles && module load wflow_wcoss

# Run smoke tests:
python3 -m pytest src/uwtools/tests/test_acorn_env.py -v

# Quick environment sanity check (no pytest needed):
python3 --version          # expect 3.12+, NOT 3.8.6
uw --version               # expect 2.16.0
which wgrib2               # expect a path
which qsub                 # expect a path
python3 -c "import xarray, netCDF4, grib2io; print('deps OK')"
```
