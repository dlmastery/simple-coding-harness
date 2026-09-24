# Lab 07.07 brief

A tiny tic-tac-toe player that learns from self-play, a saved policy table, and a frozen comparison with its untrained version.

Starting state: The distinction between retained learning and improved performance. The agent uses the local Python environment and the supplied self-play tool; no extra agent processes are needed.

Prediction to ask: If two players interact but no table values change, what has been learned?

Execution limit: 3,000 training games plus 500 evaluation games per policy: 4,000 games total, CPU only. Rule tests use separate tiny fixtures. No LLM weights change.

Follow the README steps. Keep source data and the supplied evaluation contract unchanged. Use the canonical course skills. Generate any required code yourself. Save observations, failures, and the learner’s progress in the separate workspace. Do not invent student answers, measurements, or protected evaluator access.

Acceptance: All 4,000 experiment games are retained. The table has actual updates, legal game traces, and unchanged evaluation hashes. Both policies use the declared evaluation schedules. The report separates this one measured comparison from claims about optimal play, other tasks, or RSI.
