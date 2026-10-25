# Larger experiment brief

The agent completes this document through conversation. Students do not fill out configuration fields by hand. Unanswered items remain explicit; they are not permission to guess resources or spending.

## Scientific question

State the prediction task, the hypothesis, and whether this moves an existing experiment or creates a new one. Identify the incumbent and what a valid comparison would establish.

## Inputs and evaluation

Record data location, permission, version and checksum manifest, size, target, prediction time, available features, training/selection/final partitions, preprocessing boundary, metric, and evaluation owner. Specify what the candidate can read and which boundary is technically enforced.

## Candidate and environment

Record model family, training procedure, starting checkpoint, code version, seed policy, dependencies, and result format. Distinguish a model snapshot from a complete training-resume checkpoint.

## Available compute

Record the student's authorized host or service, connection profile name, operating system, runtime, CPU/memory, accelerator type/count, storage, scheduler, allowed queue, and allowed data paths. Do not include credentials. Mark unavailable facts unknown.

## Limits

State maximum attempts, concurrent jobs, wall time, GPU-hours or equivalent resource limit, storage, inference limit, and monetary ceiling if applicable. State whether queue time counts. Define what happens when one limit is reached. The agent must not infer permission to buy compute.

## Start, stop, and recover

State the proposed tiny smoke job; checkpoint frequency; cancel mechanism; confirmation that resources stopped; retry limit; compatible resume conditions; and where interrupted records remain. Give the student plain-language entry and stop prompts.

## Evidence and acceptance

Record candidate and attempt IDs, scheduler job IDs, state transitions, versions, logs, predictions, validation, quality, costs, and rejected proposals. Define acceptance before seeing the result. Include the smaller local check and actual backend smoke checks, with their status.

## Current authorization and next action

Distinguish preparing files, running the tiny test, and launching the larger job. Record the authorization already provided and the concrete next action. A completed brief alone is not proof a job ran.
