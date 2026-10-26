"""The task suite the course runs on. RSI_BENCH=amlb (default) or mlebench.

Both expose the same interface: DATA, SPLITS, ALL, get(id), grade(id, csv),
obfuscated_description(id). A grade has `norm`, a score comparable across tasks,
and `beats_forest` (AMLB) or the above-median flag (MLE-bench) as a pass mark.
"""

import os

if os.environ.get("RSI_BENCH", "amlb") == "mlebench":
    from .mle import ALL, DATA, SPLITS, get, grade, obfuscated_description  # noqa: F401
else:
    from .amlb import ALL, DATA, SPLITS, get, grade, obfuscated_description, prepare  # noqa: F401
