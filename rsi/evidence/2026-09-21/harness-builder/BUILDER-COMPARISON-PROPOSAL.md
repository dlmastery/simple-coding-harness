# A separate experiment for a builder claim

Status: proposal only. No builder generation or additional fit is allocated to lab 10.31.

Freeze B0 and a proposed B1 before exposing two new briefs. Use the same two briefs for both builders and retain every generated package, refusal, failed setup, and result. Brief one asks for a small electricity-demand regression harness with time-based splits, lag-availability checks, MAE, and error by hour. Brief two asks for a small equipment-state classification harness with machine-group splits, balanced accuracy, explicit per-class recall, and a missing-class refusal. These are task specifications, not data that has been acquired or experiments that have run.

An evaluator separate from the builder should establish data provenance, accepted inputs, task-specific checks, compute caps, and inaccessible final cases before generation. Give each builder the same development feedback and generation budget. Generated artifacts then receive the same task execution allowance. Include generation failures in the denominator; do not evaluate only the prettiest package. Record generator tokens/time separately from generated-harness execution costs.

Assess contract correctness, successful bounded execution, required reports, rejection behavior, and task results. Keep generator, generated artifact, runtime model, and evaluator identities distinct. Two briefs can expose a local weakness but cannot establish general builder superiority. Repeated independently initialized generations and more task families would be needed for a broader claim. That expanded study requires a new protocol and budget.
