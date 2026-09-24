# Which change improves the procedure?

This study compares ordinary ML search, retained experience, a revised
harness and a revised updater. The source is frozen before fitting six
reserved classification/regression tasks. All 288 search attempts and 36
final refits have completed. The [checked report](../../../evidence/2026-09-22/tabular-comparison/README.md)
shows a memory advantage over random search, an overall disadvantage against
the fixed portfolio, and uncertain updater gains. The 10,353 final checks
verify the recorded execution; they do not establish RSI effectiveness.

![A fair comparison gives two procedures matched starting information and resources.](../../../assets/illustrations/matched-search-budgets-v1.png)

Each procedure receives four common probes and four remaining attempts.
The fixed and random controls are credible conventional alternatives. The
memory procedure reads checked earlier experience. The final three procedures
separate changes to the harness from changes to its updater.

## Two actual later rounds

The original or revised updater reads five role instructions and writes a
research skill containing two proposals. Those models run. After checking
their predictions, the updater writes a later skill from the feedback and
its next two models run. Each proposal preserves the selected parent's code,
and the trace records the exact skill and role-file hashes used.

The [original roles](roles/v0/Analyzer.md) implement conventional local
refinement. The [revised roles](roles/v1/Analyzer.md) add checked experience,
a reference check and a split between an alternative template and local
refinement. Both retain the same external selection rule. The five files are
instructions for one bounded program, not five independent LLM agents.

The root coding agent authored the changes from earlier development evidence.
This tests the candidate updater's later use during comparison. A stronger
claim about post-promotion deployment or repeated meta-generations needs
additional evidence.

## Inspect it with your coding agent

```text
Read rsi/experiments/real-tabular/comparison/README.md and the linked protocol.
Explain the fixed, random, memory, parent, harness and updater procedures.
Show how a saved research skill determines two later real fits.
Trace one child to its parent source and the updater's five role files.
Separate training, selection and final rows, then explain the shared budget.
Inspect available evidence first. Do not start another comparison implicitly.
```

The maintainer driver is `run_tabular_comparison.py` in
`how-did-i-generate-it/rsi/scripts`. It has separate prepare, search and score
actions. Its current recorded run uses a fixed sibling workspace and refuses
reuse. A reproduction needs a fresh checkout with a different parent folder,
the saved dependency versions and all pinned evidence inputs. Preserve the
completed study and its frozen source. Do not change its paths or protocol
mid-run to bypass the refusal.

The [execution protocol](../../../../how-did-i-generate-it/rsi/validation/TABULAR-COMPARISON-PROTOCOL.md)
allocates 288 search attempts and 36 final-scoring refits. Every attempt has
a 30-second subprocess limit and one thread. Failed attempts count. Search
must finish, freeze all choices and pass independent checks before final
scoring begins. Timed model runs are sequential.

## What a result can establish

A source change can leave predictions unchanged. Two operators can cancel
one another's effect, or the same incumbent can survive both searches. Check
the executed candidates and their actual results before claiming improvement.
Report predictive quality separately from compute. All six procedures have
eight search attempts, so fewer fitted candidates is not an outcome of this
study. Earlier discovery-tree evidence tests that separate question.

The comparison preserves mechanisms from the research studio. It is not a
reproduction of every named paper. Inspect the [actual later skills](../../../evidence/2026-09-22/tabular-comparison/runs/23/updater/skills/2/RESEARCH-SKILL.md)
and [composition diagnosis](../../../evidence/2026-09-22/tabular-comparison/composition/README.md).
Two changed recipes construct identical estimators after a later parameter
assignment overwrites an earlier change. The full frozen result stays intact.

The separate [refinement repair](../refinement-v2/README.md) now preserves
template-relative settings and rejects identical constructed candidates.
Its four-fit integration check and later no-fit capacity review are preserved
separately. This fixes observable behavior; it does not replace these results
or establish a stronger research procedure.
