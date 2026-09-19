"""Shared mechanics of the rsi/ tool scripts, built once and never a lesson:
the recipe space and fit, the data and the curriculum, the memory cards, the
packs (lint, versions, rollback), the graph, the search policies, the
scorecard, the trace log and the on-disk run state.

Nothing here calls a model. A coding agent (Claude Code, this repo's harness,
Antigravity, Codex) reads a lesson's SKILL.md and runs the scripts in
rsi/tools/ through its shell; the scripts are the gates, the agent is the
loop.
"""

import os

# one thread per fit: the tables are small and a 32-core OpenMP pool spends more
# time synchronising than fitting (HGB is 5x slower with the default pool here)
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")

# pandas before scikit-learn, on purpose: on some Windows machines pyarrow's DLL
# takes 30 s to load once scipy's are in the process, and sklearn imports pandas
import pandas  # noqa: E402,F401
