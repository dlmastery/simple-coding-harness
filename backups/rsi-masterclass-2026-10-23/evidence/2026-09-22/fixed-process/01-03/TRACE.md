# Actual five-action trace

Each row in TRACE.csv was written as running before its action and completed afterward. Frame and split are in-process checks; command logs record inspection, fit and prediction-check exit statuses and wall time. These intervals overlap their parent action intervals and must not be added twice.

- frame: complete; 0.001021 seconds; TASK.md; FRAME-CHECK.md
- inspect: complete; 1.891414 seconds; DATA-REPORT.md; sample.csv; data-overview.png
- split: complete; 0.035986 seconds; SPLIT.md
- fit: complete; 1.562787 seconds; CONTRACT.md; trials.csv; trial-001 artifacts
- check: complete; 1.549676 seconds; trial-001/CHECK.md
