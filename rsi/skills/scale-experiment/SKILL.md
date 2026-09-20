---
name: scale-experiment
description: Prepare an RSI course experiment for larger CPU, GPU, or cluster jobs while preserving task and evaluation rules and tracking resources. Use for optional scale-up extensions.
---

# Scale an experiment

Read the frozen scientific contract and proposed larger task. State what remains comparable and what changes. A larger dataset, model, trial count, or training budget can define a different experiment.

Read `../../compute/README.md`, `../../compute/JOB-BRIEF.md`, `../../compute/ADAPTER-CONTRACT.md`, and `../../compute/BACKEND-CHECKS.md` relative to this skill directory. Complete the brief through conversation; the learner must not handwrite configuration.

Inspect the student's actual backend without reading or displaying credentials. Obtain a concrete job specification: data location, model family, resources, concurrency, total budget, time limit, checkpoints, cancellation, result location, and resume policy. Never infer permission to buy compute.

Generate backend files and launch instructions in the learner workspace. Keep the student interface in plain language. Use the same candidate identifiers and data/evaluator versions across local and remote execution.

First run a tiny local contract test. Then use a small job on the actual backend before calling it supported. Record scheduler job IDs, GPU type, GPU-hours, wall time, retries, pre-emption, failed trials, agent cost where available, and monetary cost where supplied. Show the concrete launch plan before a costly run that lacks prior authorization.

Check cancellation and resumption. Do not resume from a checkpoint with incompatible data, model, or evaluator versions. A resumed attempt keeps its accumulated cost and identity.

For asynchronous search, account for completion-order bias and stale proposals. Faster jobs must not receive an unnoticed larger selection budget. Preserve failed and unfinished jobs in comparisons.

Label generated-only adapters as untested. A laptop simulation of GRPO or harness–model co-evolution does not validate distributed LLM training.
