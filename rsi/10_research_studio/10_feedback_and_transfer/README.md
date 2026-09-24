# Feedback, memory, and compatibility

[Research studio](../README.md) · [Course](../../README.md)

**You are here:** Theme 10 → research group 10 of 00–12 → labs 10.32–10.34. [Studio overview and mindmap](../README.md) · [Whole-course map](../../COURSE-MAP.md#theme-10).

Compare raw events with compact memory, distinguish action hints from richer observations, and test a local interface mismatch. These small checks make it easier to read training papers without mistaking a prompt intervention for a parameter update.

![The same inventory events are supplied as raw history, a checked summary plus later events, or a deliberately faulty summary. An independent checker computes the true final count from original events; a blank ledger compares five actor attempts.](../../assets/illustrations/memory-interface-v2.png)

*These counts are a synthetic teaching example. After adding three and removing one, the checkpoint is two; adding two more gives four. The faulty summary omits the removal. Do not pre-fill the actor’s answer or supply the checker’s result in its input. The two extra-description conditions change wording, not state transitions. The drawn counters and tally frame are props; the explicit event tape defines the arithmetic. This external-memory exercise does not reproduce S3Gym’s game or training protocols, and a shorter representation is not presumed better.*

[Open the illustration at full size](../../assets/illustrations/memory-interface-v2.png).

Recompute the checkpoint and final state from the event tape. Identify what the faulty summary lost without assuming an actor answer. The next two figures change supplied feedback and response format; neither local exercise updates model weights.

**Start with:** The tutor creates exact-checker fixtures with explicit budgets. Bring the earlier information-boundary and model/harness distinctions.

- [10.32 · Compare raw history and summarized memory](step_32_memory_interface/README.md): A tiny state-tracking task with an exact checker and two memory representations.
- [10.33 · Compare action hints and richer observations](step_33_scaffolding/README.md): A small task comparison with action guidance, observation enrichment, and assistance removed.
- [10.34 · Keep model training aligned with its harness](step_34_model_harness_fit/README.md): An interface-mismatch experiment and a source audit of local versus whole-trajectory correction.

**Carry forward:** Keep all memory conditions, assistance traces, and parser failures. Identify which claims require actual weight training beyond these classroom exercises.

Read the source connection in each lab. The required path fits a laptop; actual large-model training is an optional, separately planned extension.
