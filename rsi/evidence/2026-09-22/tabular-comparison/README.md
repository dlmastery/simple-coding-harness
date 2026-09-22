# Experience helps some searches; the fixed portfolio remains strongest

This completed study compares six ML research procedures on six reserved
public tasks. Each procedure gets the same four probes and eight total
search attempts. Its selected model is frozen before final scoring.

**Memory beats random search in this sample, but loses to the stronger fixed
portfolio overall. The revised updater has an uncertain mean advantage over
the original updater using the revised harness.** This is not an established
RSI effectiveness result.

![All six procedures on every task, showing balanced accuracy or MAE.](native-score-comparison.png)

The bars use measured final scores. Higher balanced accuracy is better;
lower MAE is better. Read the [complete numerical report](REPORT.md), including
the unfavorable comparisons. [Native scores](NATIVE-SCORES.csv),
[normalized scores and costs](SUMMARY.csv) and [paired rows](PAIRED-TASKS.csv)
remain available for reanalysis without fitting again.

## What changes between procedures

| Procedure | What determines its last four experiments? |
|---|---|
| Fixed | A conventional diverse portfolio, declared before fitting |
| Random | Seeded draws from the full revised builder space and bounded parameters |
| Memory | Candidate ranks learned from checked outcomes on separate development tasks |
| Parent | The original updater produces two rounds of local model refinements |
| Harness | The same updater uses revised representation and objective operators |
| Updater | Revised role instructions divide each later round between experience and local refinement |

The root coding agent wrote the harness and updater changes. A bounded
program generates the inner proposals. The five role files are actual inputs
to that program; they are not five independent LLM agents. No model weights
are updated to learn the research strategy.

The [protocol](../../../../how-did-i-generate-it/rsi/validation/TABULAR-COMPARISON-PROTOCOL.md)
was frozen before any of these tasks were fitted. Development used six other
tasks and 96 fits. The [data guide](../real-tabular-data-v2/README.md) explains
source exclusions, duplicates, row splitting and prior exposure. Naval
propulsion data come from simulation. The classroom partitions are not an
official benchmark run.

## Separate each claim

| Prespecified contrast | Better / tied / worse tasks | Mean normalized loss change | Exploratory 95% interval |
|---|---:|---:|---|
| Harness minus parent | 1 / 4 / 1 | +0.003042 | [−0.003393, +0.012519] |
| Updater minus harness | 2 / 3 / 1 | −0.009343 | [−0.021838, +0.002262] |
| Memory minus fixed | 1 / 2 / 3 | +0.014333 | [+0.002969, +0.024115] |
| Memory minus random | 3 / 3 / 0 | −0.009496 | [−0.019082, −0.001958] |

Negative loss change favors the first procedure. These intervals resample
only three classification and three regression tasks. They do not account
for multiple comparisons, model-seed variation or arbitrary task selection.
The updater and harness intervals include zero. The memory result depends
on which conventional control we use; both belong in the conclusion.

Each procedure actually spends eight search fits per task. **There are no
saved fits in this study.** The earlier [discovery-policy comparison](../discovery-final/README.md)
tests a different question and does show lower executed search work.

## Follow one updated skill into later work

Start with task 23, contraceptive method classification. The
[first later skill](runs/23/updater/skills/1/RESEARCH-SKILL.md) reads the four
probe outcomes and schedules two candidates. Neither beats its incumbent.
The [next skill](runs/23/updater/skills/2/RESEARCH-SKILL.md) records the prior
skill hash and all six observed attempts, then schedules two further fits.
Step seven uses the next experience-ranked template. The
[ledger](runs/23/updater/LEDGER.csv) records its improved selection result,
and [retention](runs/23/updater/skills/2/RETENTION.md) preserves it.

The [step-seven source](runs/23/updater/attempts/07/builder/candidate.py),
[parent source](runs/23/updater/attempts/07/PARENT-CANDIDATE.py) and
[role-read record](runs/23/updater/skills/2/ROLE-READS.csv) connect the decision
to the inherited implementation. Later final scoring gives balanced accuracy
0.548682 for the updater versus 0.514592 for the revised harness with the
original updater. This favorable task illustrates the trace; it does not
replace the full six-task comparison. On German credit, the updater instead
falls from 0.709740 to 0.702954.

This demonstrates trial use of the revised updater across later skill rounds.
It does not establish post-promotion deployment, autonomous invention,
multiple successful meta-generations or recursive acceleration.

## Why different source can still give the same model

The [post-run composition audit](composition/README.md) constructs the 288
recorded recipes without fitting. Two later parent/harness pairs have
different candidate source but identical complete estimator settings. A
template changes the minimum leaf size, then the capacity operator overwrites
that setting. The syntax changed while the effective estimator did not.

No identical-constructor repeats were found within an individual eight-fit
procedure. This is a cross-procedure cancellation, not evidence that every
arm reran the same eight models. Other ties arise because both searches keep
the same incumbent. Source identity, changed behavior and better performance
need separate evidence.

The frozen study remains unchanged. A future revision should check composed
behavior before fitting, preserve the conventional portfolio as a serious
control, and use new evaluation tasks. These final scores cannot become a
tuning signal while retaining their status as untouched evaluation.

## Checks, cost and source-method limits

All **288 search attempts and 36 scoring refits** succeed. Before scoring,
9,485 search checks pass; the final audit passes 10,353 checks including
recomputed predictions, exact source inheritance, skill use, frozen choices
and reproduced selection scores. The [search checks](SEARCH-CHECKS.csv),
[final checks](FINAL-CHECKS.csv) and [choice freeze](CHOICE-FREEZE.csv) are
retained. Passing checks establish the listed invariants, not general efficacy.

Search consumes 709.242 worker-process seconds; scoring consumes 83.241.
The preceding 96 development fits, memory compilation and replay, and
unmetered coding-agent inference are additional. This is not total research
cost. Data separation is procedural on a shared filesystem.

This study complements the memory, AIDE-inspired harness and MetaSkill
lessons. It is not a reproduction of Recuris, RSIAgent, AIDE2 or MetaSkill.
Their source-specific mechanisms and omissions stay documented in the
research studio. Dream-style history-tree replay and online discovery remain
in their separate archives rather than being renamed as this ranking memory.

## Inspect this with your agent

```text
Read this report and the frozen protocol.
Explain each procedure and its control.
Trace the two later skills for task 23.
Recompute one saved final metric without fitting.
Then inspect German credit and the composition audit.
Explain why a useful memory, a changed updater and
a successful recursive improver are different claims.
Do not start new fits or edit this evidence archive.
```

The [archive manifest](ARCHIVE-MANIFEST.csv) records original file bytes.
Frozen runtime sources are in `source`; post-run reporting tools are in
`analysis-source`. Earlier chart versions remain in `visual-drafts`.
The figure was reviewed for labels, units and completeness; the small naval
errors use six decimals so visible rounding does not create false ties.
