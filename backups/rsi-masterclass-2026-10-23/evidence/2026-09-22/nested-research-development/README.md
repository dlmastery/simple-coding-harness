# A small development gain from a rewritten researcher

**I1's generated researcher improved two tasks and tied four.** Its mean
normalized evaluation-loss change was −0.002142 against the parent. That
narrowly passed the predefined development gate of −0.002 with at least four
non-worse tasks. I0 tied all six and its child was rejected.

These are previously exposed development tasks, not fresh transfer evidence.
The exploratory task-bootstrap interval for I1 is [−0.003906, 0.000000].
It includes zero. [Read every native score and the analysis](REPORT.md).

| Development task | Parent balanced accuracy | I1 balanced accuracy |
|---|---:|---:|
| Contraceptive method choice | 0.533812 | 0.538851 |
| German credit | 0.706604 | 0.714416 |

Letter classification and all three regression tasks tied. Every score remains
in [NATIVE-SCORES.csv](NATIVE-SCORES.csv); none was dropped from the gate.

## What actually changed

The parent researcher starts with eight model families or configurations, then
spends four attempts on incumbent refinements. I1 rewrites the executable
researcher to preserve that initial coverage, try unused alternatives and
refine two distinct families. The complete generated loop runs after the
rewrite; a saved instruction alone does not count as execution.

[BEHAVIOR-CHANGES.csv](BEHAVIOR-CHANGES.csv) compares the actual constructed
models. I1 changed three of twelve choices on the letter task and four on each
other task. I0 changed three choices on one task and none on the other five.
This explains why changing source does not automatically change outcomes.

Both children are bounded, programmatically generated researchers. Their
templates, mutation rules and rewrite space were authored by the root coding
agent. There are no independent LLM researchers or model-weight updates.

## The inherited improver was used again

After scoring, the unchanged external rule selected I1's child and retained
the original parent for I0. Both frozen improvers then generated a second
complete researcher from their respective retained parent and the first
generation's actual search traces:

- [I0 generation two: source](generations/2/i0/researcher.py) and
  [parent, evidence and improver hashes](generations/2/i0/GENERATION.md).
- [I1 generation two: source](generations/2/i1/researcher.py) and
  [parent, evidence and improver hashes](generations/2/i1/GENERATION.md).

[VERDICTS.csv](VERDICTS.csv) records the decisions. The
[22 later-generation checks](GENERATION-CHECKS.csv) independently reconstruct
the gate, verify parent and improver identities, and check that the new
researcher's ranking and multiplier use the recorded outcomes. These sources
still need the reserved-task execution. Generation is not yet transfer or
post-promotion deployment evidence.

## Execution and limits

All **216 search attempts and 18 scoring refits succeeded**. The independent
audit passed 6,245 search checks and 6,555 final checks; the final count includes
the search checks. Choices were globally frozen before scoring. Saved rows,
truth, predictions, constructor identities, inherited source and proposal replay
match. No retries or shared-fit cache were used.

Recorded worker-process time was 485.393 seconds. All losing searches are
charged. This excludes agent inference and host analysis, so it is not a claim
of lower total research cost. See [COSTS.csv](COSTS.csv).

The former final partitions of these public tasks are now development
evaluation. The next comparison must use the six reserved datasets, unchanged
generated researchers, and the fixed and random controls declared in the
[protocol](source/NESTED-RESEARCH-PROTOCOL.md). No adaptation to their final
scores is permitted. The earlier all-zero comparison remains preserved.

The [preparation archive](../nested-research-preparation/README.md) preserves
the first zero-fit constructor-exhaustion failure. This archive also retains
the corrected preflight and its initial checker error. Synthetic fixture
outcomes are labelled and are not included in measured scores or fit costs.
[ARCHIVE-MANIFEST.csv](ARCHIVE-MANIFEST.csv) covers the original files; this
authored report and the manifest are additional publication files.
