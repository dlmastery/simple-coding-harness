# What was retained, read, and answered

## A rejected procedure leaves useful knowledge

The two wiki fixtures accepted the proposed fallback's decision on seconds but rejected its decision on ticks. The gate therefore kept ACTIVE-SKILL.md unchanged. TRACE.md and the copied prior evidence also stayed unchanged. NOTEBOOK.md gained a scoped, source-linked observation; NOTEBOOK-v0.md preserves its previous version. The failed proposal remains available without becoming active.

The evaluator parsed the proposed skill once and reused that configuration for the two cases. Each case input was read from its saved CSV. The per-case READS.csv lists the consumed skill/input identities; it is not a transcript of two independently initialized agent contexts or a complete operating-system I/O audit. The skill is also read to calculate its recorded hashes. The notebook was not supplied to the task-decision function.

The separate exposure condition read the accepted active skill and the updated notebook into one packet. It produced no third answer. That demonstrates a changed information interface, but provides no performance comparison. The author already had access to all evidence and both skills. The raw layer is maintained as immutable by procedure and verified hashes, not protected by an inaccessible filesystem.

## A faulty summary changes the represented state

The coding agent read all five saved packets in one tool invocation, then authored one answer file per packet. Each answer uses the arithmetic implied by that representation, within the 60-word cap. The checker, run afterward, computes the final count from ORIGINAL-EVENTS.csv.

| Condition | Packet words | Answer | Original-event answer | Check |
|---|---:|---:|---:|---|
| Raw events | 68 | 8 | 8 | Pass |
| Correct summary and tail | 58 | 8 | 8 | Pass |
| Faulty summary and tail | 58 | 11 | 8 | Fail |
| Expanded raw descriptions | 644 | 8 | 8 | Pass |
| Correct summary and expanded tail | 346 | 8 | 8 | Pass |

Word counts use whitespace, not provider tokenization. The correct checkpoint retains six crates. The faulty one says nine because it omits the fourth event's removal of three crates. Applying the same tail then preserves that three-crate error. The failure is a deliberately constructed representation error, not an independently observed failure of this agent to remember its own history.

The expansion added descriptive text without changing operations. Both corresponding answers stayed correct in this one shared-context exercise. This cannot establish that summary memory is generally better, more efficient, or more robust to long contexts. The author designed the sequence, knew the expected outcome, and could see every condition. There is no clean memory ablation or technical answer secrecy.

## Scope

These activities demonstrate separate retention rules and an information-loss mechanism. They do not train weights, reproduce the source systems, test independent agents, or establish learner understanding. SOURCE-AUDIT.md records the primary-method connection. A stronger memory comparison would require isolated contexts, unseen sequences, repeated conditions, and measured inference resources. None of those extensions ran in this allocation.
