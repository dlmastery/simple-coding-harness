# Scaffolding author walkthrough

Lab 10.33 uses a constructed three-field experiment form. Inspect a field, repair the missing value, and submit to an exact checker. No model fits or parameter updates occur. This is an author walkthrough; learner prediction, quiz, and teach-back are unattempted.

Four attempts are allowed, each with at most three field inspections, one repair, and one final check. Task-required values are visible in every packet. Initial form values are available through the inspection command. The first two attempts share the same initial form and required values. One offers an action hint; the other adds a statement about the current state. The fresh unassisted form changes the dataset, split, metric, and missing field. The stale-hint form has correct observation enrichment and an outdated action hint.

The actor is the current coding agent. It must invoke inspection and repair tools explicitly; the driver must not select the missing field or generate an answer. Record all successful tool calls and exact outputs. A final check compares all fields with the declared requirements and checks that initially correct fields remain unchanged. The original fixture, packets, and controller are hashed before the first attempt.

Author prediction before execution: all four can pass because required values are explicit. Deliberately following the stale hint first should add an unnecessary inspection. This is a constructed demonstration, not a spontaneous agent failure. The same author writes the fixtures and acts on them in a shared conversation, with knowledge of all conditions. Fresh means a different fixture, not an uncontaminated context. No causal estimate of learning or scaffold superiority can follow.

Execution order: action hint, enriched observation, fresh unassisted, stale hint. No retries after the final check. No extra task attempts during publication. Provider inference cost is unavailable; inspection counts describe only this local interface.
