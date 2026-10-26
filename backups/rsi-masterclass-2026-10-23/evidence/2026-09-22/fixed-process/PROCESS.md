# Run one fixed bike baseline

Use the existing project Python 3.12 environment. Keep the supplied public source intact. This process has no outer search loop.

| Action | Input | Output | Completion check |
|---|---|---|---|
| Frame | TASK.md and bike data card | Copied TASK.md and FRAME-CHECK.md | Target is cnt; unit is rentals per hour; outcome components are excluded; this is retrospective prediction |
| Inspect | Pinned hour.csv | DATA-REPORT.md, sample.csv, data-overview.png | Source hash matches; report states dimensions, missingness, chronological roles and public-data boundary |
| Split | Task's date rule and source dates | SPLIT.md | 2011 trains; first half of 2012 selects; second half is final; sets are disjoint and complete |
| Fit | Fixed recipe below, training rows and one-attempt allowance | Trial proposal, registry, result and selection predictions | One successful constant/calendar fit, seed 17; no search or final evaluation |
| Check | Selection predictions, source targets, row identities and registry | CHECK.md, action trace and progress | Separate calculation passes; retain outputs, actual costs and stop |

The split rule is already stated in TASK.md before inspection. The Split action checks and records that rule before fitting; it does not choose the rule after seeing a score. Fit preprocessing on training rows only. The supplied tool implements the training-median baseline and the declared partitions.

## Fixed recipe

- Task: bike
- Model: constant
- Features: calendar
- Seed: 17
- Attempts: 1

Refuse a changed source, target, metric or split. Keep failed admitted attempts. A missing output is a reason to inspect the existing state, not permission to fit again. Save timestamps and command status at each action. Public source access and separate checker code do not establish evaluator isolation.
