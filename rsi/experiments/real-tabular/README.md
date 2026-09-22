# Improve a research procedure on public tables

This extension starts with classification and regression tasks whose rows
have documented provenance. First establish a credible fixed portfolio. Then
use its development feedback to propose changes to the procedure. Compare
the frozen procedures on reserved tasks before claiming transfer.

![A discovery tree separates proposed experiments, observed evidence and later choices.](../../assets/illustrations/discovery-tree-evidence-v1.png)

This is a conceptual illustration. The current completed stage is the
eight-model baseline, not a completed recursive method comparison.

The [data guide](../../evidence/2026-09-22/real-tabular-data-v2/README.md)
explains exclusions, duplicate groups, exposure and row roles. The
[48-fit baseline](../../evidence/2026-09-22/real-tabular-baseline/README.md)
provides actual predictions and independently checked scores.

## Run the baseline through your coding agent

Ask the agent:

```text
Read rsi/experiments/real-tabular/README.md and the linked development protocol.
Explain the six development tasks, the eight-model control and the row roles.
Inspect the published results with me before proposing another run.
If we need a reproduction, create a fresh sibling workspace and execute
run_real_tabular_baseline.py, then check_real_tabular_baseline.py.
Keep all attempts, including failures. Use no final rows or reserved tasks.
Explain why this baseline is model selection rather than RSI.
```

The scripts live in `how-did-i-generate-it/rsi/scripts`. The agent checks the
saved environment requirements and invokes them with the repository's Python
environment and an absolute sibling-workspace path. Each run admits 48 fits,
one thread each, with a 30-second subprocess limit. No automatic retry exists.
Do not start a second run while another timed comparison is active. See the
[development protocol](../../../how-did-i-generate-it/rsi/validation/REAL-TABULAR-DEVELOPMENT-PROTOCOL.md)
before changing any budget or interpreting results.

## What to notice

Learned transforms see training rows only. Selection feedback chooses a
candidate. The future evaluator has a different role: it checks whether the
choice generalizes. Editing a task model, a retained research rule, a harness
builder and the updater are four different interventions.

Why can selecting the best of eight models exaggerate progress? Because the
same selection rows guide the choice. A reserved comparison tests whether the
procedure's advantage survives new evidence. Saving a new instruction alone
does not show that later work used it.

Next: declare an agent-authored revision from this development feedback,
preserve its ancestry, and test its effect. The older synthetic harness
revision remains rejected; this extension does not change that decision.
