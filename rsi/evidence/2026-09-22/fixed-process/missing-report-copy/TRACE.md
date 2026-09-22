# Actual five-action trace

Each row in TRACE.csv was written as running before its action and completed afterward. Frame and split are in-process checks; command logs record inspection, fit and prediction-check exit statuses and wall time. These intervals overlap their parent action intervals and must not be added twice.

- frame: complete; 0.000728 seconds; TASK.md; FRAME-CHECK.md
- inspect: complete; 1.938036 seconds; DATA-REPORT.md; sample.csv; data-overview.png
- split: complete; 0.038351 seconds; SPLIT.md
- fit: complete; 1.579272 seconds; CONTRACT.md; trials.csv; trial-001 artifacts
- check: complete; 1.537627 seconds; trial-001/CHECK.md
