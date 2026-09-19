"""Shared mechanics of the rsi/ series, built once and never a step: the recipe
space and fit, the data and the curriculum, the budget, the locked test, the
trace log, the memory cards, the packs (lint, versions, rollback), the graph,
the approval cycle, the tool table with execute(), the skills harness, the
fake model and the curriculum runner. Every step directory holds packs, tests
and a run.py - never a loop of its own.
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
