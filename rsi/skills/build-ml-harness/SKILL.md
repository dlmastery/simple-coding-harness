---
name: build-ml-harness
description: Generate a small runnable ML research harness from a plain-language task brief, with tools, checks, budgets, and an inspectable workflow. Use in meta-harness lessons or a new tabular task.
---

# Build an ML harness

Read the learner's brief. Extract the prediction unit, target, available inputs, data source and permission, metric, split, budget, expected outputs, and forbidden changes. Resolve an ambiguous scientific choice before training; routine implementation choices are yours.

Create the harness in a new learner-workspace folder. Generate code and configuration yourself. The student edits ordinary language only. Produce a short `README.md`, `TASK.md`, `WORKFLOW.md`, tools, evaluator, tests, dependency record, and a recovery guide.

The workflow must frame the task, inspect data, validate splits, fit a simple baseline, propose a bounded change, evaluate it, and retain or reject it. Include failure paths and stop rules. Use the supplied shared tools when they fit. Do not copy a regression metric into a classification task.

Generate meaningful checks for data leakage, altered metrics, mismatched candidates, failed attempts, and budget exhaustion. Actually run a baseline and an intended rejection. Save command exit status and resulting reports. A generated script without execution is unfinished.

Explain which decisions came from the brief, which came from this builder, and which the generated harness makes at run time. The builder is a meta-harness because it creates a harness. It is not recursive self-improvement merely because it generated files.

Keep task and evaluator contracts separate from compute. Default to local CPU. Use the scale skill for a larger backend. Record support honestly: generated, inspected, locally tested, or tested on the target backend.
