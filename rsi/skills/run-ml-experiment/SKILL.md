---
name: run-ml-experiment
description: Run one bounded tabular ML experiment for the RSI course, with frozen task rules, a hypothesis, retained failures, and readable evidence. Use for regression and classification activities in this course.
---

# Run an ML experiment

Read the task data card, current lesson, [tool notes](../../tools/README.md), and workspace progress. Confirm the task, prediction setting, metric, permitted features, split, and remaining budget before fitting.

Write a one-sentence hypothesis. Name the one intentional difference from the comparison candidate. Use the supplied tool for standard models. Generate additional code only when the lesson needs it; keep that code and its contract in the learner workspace. Do not edit the shared evaluator to improve a score.

Use project-local Python. Invoke one `run` operation with explicit task, model, features, seed, hypothesis, and absolute workspace. On the first fit, pass the lesson's total workspace budget through `--attempt-limit`. Later processes recover that frozen limit; do not increase it on resume. If following a retained skill, read it first and pass its path for a snapshot. Record in `DECISION.md` which instruction caused which choice. A snapshot alone proves only which file was recorded.

Apply a 60-second command timeout. If interrupted, inspect the process and preserve the attempt. Never run concurrent writes into one workspace. Never delete failed trials or refund their costs. Limit this skill invocation to one candidate unless the learner explicitly requests the lab's bounded loop.

Inspect the exit status and actual result. Recompute a small prediction error by hand when teaching MAE. For classification, inspect both class recalls. Compare only candidates with the same task contract. Keep weak results and state uncertainty.

Do not use the final partition during proposal or selection. A final evaluation is a separate lesson step that closes selection. The source is public, so state the limit of this boundary. Stronger evaluation needs an independently controlled service with inaccessible cases.

Record source hashes, package versions, model settings, seed, fit time, attempted candidates, invalid candidates, and available agent cost. Mark unavailable costs as unknown. A fit-only budget is not total research cost.

For a new process, reproduce the retained recipe from the frozen data and settings. Do not load an untrusted serialized model. For a larger model, ask the scale skill to prepare a reviewed backend plan before launching it.
