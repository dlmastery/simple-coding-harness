# Generated checker result

This is an author walkthrough of 01.04, not a learner session. A newly generated Python standard-library checker imports neither the supplied solver nor its checker. The author inspected the lesson, prior records and the source partition definition. This is separate implementation in the same author context, not a blinded independent review.

| Input | Observed result | Exit | Process wall seconds |
|---|---|---|---|
| Original baseline copy | 4,358 selection rows pass; MAE 159.94791188618632 | 0 | 0.1634036 |
| One substituted ID | Refused: row 0 is outside selection | 2 | 0.1428178 |

The source ID changed from 8645 to 0 at prediction row zero. ONE-CELL-DIFF.csv records the cell comparison. Source row 0 is a 2011 training row. Predictions, copied targets and hours remain unchanged. The archived original is never edited. SOURCE-IDENTITIES.csv compares five copied inputs with their archived originals.

The checker compares candidate and recipe fields, policy hash, contract, pinned source hash, complete unique selection membership, source target values, hours, finite numbers and recomputed MAE. It checks the unrounded registry score within absolute tolerance 1e-10. Candidate references are fixed to this baseline; this is not a general-purpose authentication service.

Exactly two checker subprocesses ran, with a 60-second timeout each. Zero model fits, no new inference predictions, no final evaluation. Their process intervals total 0.3062214 seconds; this excludes preparation, author reasoning and model-service cost. Python 3.12.12 on the current Windows host; standard library only.

## What a lone metric cannot establish

If given only 159.95, the checker cannot recompute errors, establish which rows were used, match targets to the source, detect omissions or duplicates, or establish which recipe produced the predictions. This is the additional-change explanation; no third checker invocation was made.

Even the complete artifact check cannot prove that the claimed fitting process ran, that the author lacked evaluation access, or that the model generalizes. Hashes expose a changed reference only if the expected reference remains trusted. Solver, checker and author share host access. Tests of every other implemented refusal are outside this two-run activity.

## Preparation and review

Read-only discovery encountered guessed absent paths (guidance-foundations.mjs, tasks.py and rsi/data) and a PowerShell literal glob error. Subsequent discovery located lesson-guidance.mjs and the actual source/partition definition. No checker invocation or fit occurred during those searches.

Both declared checker invocations ran once with expected outcomes. A later PowerShell archive-preparation command failed at parsing because its nested for/foreach block lacked a closing brace. It executed no statements and did not rerun either check. The command was replaced by a simpler cell comparison; this records the failure rather than hiding it.

The existing row-identity-check-v1 illustration was visually inspected at full size. Its symbolic S/T identities, same-reference arrows and caption fit this activity. It remains unchanged. The real substitution is 8645 to 0; the illustration does not claim those literal IDs.

Learner prediction, quiz and teach-back remain unattempted. Generated code and actual reports close the author checker-generation gap; no student response is inferred.
