# Commands used for the maintained entry path

Working directory: the repository root. The agent used the project Python.

1. Run how-did-i-generate-it/rsi/scripts/diagnose_nested_outcomes.py with
   --output C:/Users/abhir/Documents/Codex/2026-09-19/lo/work/rsi-work-2026-09-22-nested-entry-review/reports.
2. Repeat with the same output path. Expect exit 1 and unchanged report bytes.
3. Use --output relative-learner-report. Expect argument error exit 2.
4. Compare the three report CSV hashes with nested-outcome-diagnosis.
5. Run the retained trace-inheritance.ps1 with the repository and output paths.
6. Select the first differing prediction for spam and housing, and the first
   prediction for DNA. These are chosen teaching rows, not a random sample.

No training command, study restart or final-scoring worker was invoked.
