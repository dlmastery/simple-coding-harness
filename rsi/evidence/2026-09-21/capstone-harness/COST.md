# Count actual work separately from setup and fixtures

Actual fits: two median regressors, one in the original package and one in a clean export. Their recorded fit times are 0.0013130000152159482 and 0.0011767999967560172 seconds. These tiny numbers exclude startup, setup, author reasoning, checks, and orchestration; they are not end-to-end research cost.

One separate fit-failure stub admitted and charged a simulated attempt but did no model training. Its failed row remains in guard-cases/fit-failure-stub/ATTEMPTS.csv. Seven other guard cases inspect altered copies and do not fit models. Three external invalid requests were refused with exit 2 and no fit admission.

All driver subprocess wall times, including failures and installation retry, are in the COMMANDS CSV files. Fit time is nested inside process time; do not add it again. Installation and dependency inspection costs are real setup work, even though they do not consume fit allowance.

Agent inference cost, author time, peak memory, electrical use, and monetary total are unknown. No paid compute job or GPU launch occurred. A proposed larger-backend plan is not a cost measurement.
