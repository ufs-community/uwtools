# ecflow & Python Version Issues — Notes for uw-tools Team Discussion

**Branch:** `acorn_testing`
**Date:** 2026-07-24
**Context:** Getting uwtools approved on WCOSS2 (Acorn test environment).
Currently working through v2.16.0 approval; will need v2.17.0+ for ecflow_tool.

---

## The Two Root Problems

### Problem 1 — Python Version Mismatch (Runtime)

WCOSS2 ships Python 3.8.6 as the system Python. The ecflow package on WCOSS2 is a
compiled C++ extension (`.so` file) that was built specifically against Python 3.8.6.
You cannot load a `.so` built for Python 3.8 from a Python 3.12 interpreter —
the OS-level ABI is incompatible and the interpreter will refuse to load it.

| | Version |
|---|---|
| WCOSS2 system Python | 3.8.6 |
| WCOSS2 ecflow compiled against | 3.8.6 |
| uwtools aigfs venv target | 3.12+ |
| uw-aigfs `environment.yml` (current) | 3.14.* |

There is no workaround short of either:
- Recompiling ecflow against the target Python version (requires WCOSS2 admin), or
- Running ecflow-dependent code from the system Python 3.8.6 (defeats the venv)

**This is a runtime issue.** The venv installs cleanly. Nothing breaks until Python
actually tries to load the ecflow shared library.

---

### Problem 2 — ecflow API Version Mismatch (Runtime)

Even if the Python version were aligned, WCOSS2 has ecflow **5.6.x**.
The uwtools `ecflow_tool` (added in v2.17.0) was written against the ecflow **5.15.x**
Python API. The API changed significantly between these versions — suite definition
objects, scheduler attributes, and repeat types were all restructured.

| | Version |
|---|---|
| WCOSS2 system ecflow | 5.6.x |
| uwtools ecflow_tool requires | 5.15.x |

`uw ecflow realize` would fail at the API call level even if ecflow imported
successfully. This is also a **runtime issue**.

---

## The Critical Blocker Specific to v2.17+ (Our Upgrade Path)

**This is the item that needs to go to the uw-tools team.**

In v2.17+, `cli.py` has this at the **top of the file**, outside any function:

```python
# src/uwtools/cli.py, line 24
import uwtools.api.ecflow
```

And `uwtools/ecflow.py` has this at its **top level**:

```python
# src/uwtools/ecflow.py, lines 13–27
from ecflow import (
    Defs, DState, Family, Late, Node,
    RepeatDate, RepeatDateTime, RepeatDay,
    RepeatEnumerated, RepeatInteger,
    Suite, Task,
)
```

### The import chain when you run any `uw` command:

```
uw (entrypoint)
 └── cli.py is loaded
      └── import uwtools.api.ecflow          ← top-level, line 24
           └── from uwtools.ecflow import ... ← top-level
                └── from ecflow import Defs, Suite, ...  ← FAILS on WCOSS2
                     (ecflow .so built for Python 3.8.6, venv uses 3.12)
```

**Result:** `uw` crashes with an ImportError before doing anything at all.
This is not just an ecflow subcommand problem — it breaks `uw config realize`,
`uw execute`, `uw fs`, and every other command.

**v2.16.0 is safe** because ecflow_tool was not added until v2.17.0.

---

## What to Ask the uw-tools Team

### Core ask: make the ecflow import lazy

The import is currently **eager** (fires at module load time). The standard Python
pattern for optional or platform-specific dependencies is a **lazy import** —
move the import inside the function that actually needs it, so it only runs when
the ecflow subcommand is explicitly invoked.

**What the fix looks like in `cli.py`:**

```python
# Current (eager — breaks uw on WCOSS2):
import uwtools.api.ecflow           # top of file

# Fixed (lazy — only runs when ecflow subcommand is called):
def _ecflow_realize(args):
    import uwtools.api.ecflow       # inside the function
    return uwtools.api.ecflow.realize(...)
```

**What the fix looks like in `uwtools/ecflow.py`:**

```python
# Current (eager — hard import at module level):
from ecflow import Defs, Suite, Task, ...

# Fixed option A — lazy inside each function that uses ecflow:
def realize(...):
    from ecflow import Defs, Suite, Task, ...
    ...

# Fixed option B — TYPE_CHECKING guard for type hints, lazy at call time:
from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from ecflow import Defs, Suite   # only for type checkers, not at runtime
```

### The practical question to bring to the team:

> "For WCOSS2, ecflow is not importable from our Python 3.12 venv due to a
> Python ABI mismatch (WCOSS2 ecflow 5.6.x was compiled against Python 3.8.6).
> In v2.17+, `cli.py` eagerly imports `uwtools.api.ecflow` at startup, which
> causes `uw` to crash on import before any command runs.
>
> Can the ecflow import in `cli.py` and `uwtools/ecflow.py` be made lazy, so
> that the rest of uwtools works on systems where ecflow isn't available or has
> an incompatible Python build?"

---

## Short-Term Workaround for the NRT Demo (Already Planned — Phase 2 Task 2)

For the near-RT demo, `uw ecflow realize` does **not** need to run on WCOSS2.

1. On **Ursa** (has ecflow 5.15.x, compatible Python): run `uw ecflow realize`
   against `ush/wcoss_config.yaml` to produce the suite `.def` file
2. Commit the rendered `.def` to the repo (e.g. `parm/wflow/wcoss_suite.def`)
3. On WCOSS2: use `ecflow_client --load wcoss_suite.def` directly — no Python,
   no uwtools at that step

**This only works cleanly with v2.16.0.** With v2.17+, the CLI startup crash
means the workaround is irrelevant — `uw` won't start at all unless the lazy
import fix is in place.

---

## Summary Table

| Issue | Type | Severity for v2.16.0 | Severity for v2.17+ | Fix |
|---|---|---|---|---|
| ecflow `.so` built for Python 3.8.6 | Runtime | Not a blocker (no ecflow in CLI) | **Blocks `uw` entirely** | Lazy import in cli.py + ecflow.py |
| ecflow API 5.6.x vs 5.15.x required | Runtime | Not a blocker | Blocks `uw ecflow realize` | Pre-generate .def on Ursa |
| `uw ecflow realize` can't run on WCOSS2 | Runtime | N/A | Workaround available | Pre-generate .def on Ursa |

**Bottom line:** v2.16.0 is safe to deploy on WCOSS2. The path to v2.17+ requires
either the lazy-import fix from the uw-tools team, or a new ecflow build on WCOSS2
against a compatible Python version.
