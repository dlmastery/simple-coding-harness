# Keep the reported comparisons separate

Primary reading: [ScienceBuddy v1](https://arxiv.org/html/2609.17523v1), sections 2.2–2.5, 4.2–4.4, and 7.2–7.3. These are paper-reported results, not reproduced measurements.

| Study | Metric and evaluation | Attempts | Before → after | Section |
|---|---|---:|---|---|
| Coupled | Held-out accuracy | 1 | 42.2% → 73.3% | 4.2 |
| Harness only | Separate validation, first response | 1 | 31.1% → 51.1% | 4.3 |
| Model only | Common-panel problem coverage | 4 | 48.3% → 67.8% | 4.4, 7.3 |

PAPER-ARITHMETIC.csv computes changes from these rounded inputs. The first gain is 31.1 percentage points, approximately 73.70% relative to its starting value. Coverage permits several attempts and is not single-attempt accuracy.

Feedback provenance differs: real researcher interactions in 4.1, bounded procedural simulation in 7.2, and rollout evaluation rewards in 7.3. The reflector stays fixed. Our interpretation: coupled task-model and harness gains do not establish a stronger reflector.

Section 4.2's heading says two cycles; its setup and Figure 8 describe three. The course follows the explicit setup while recording this inconsistency.

Scoped headline: the authors report improved scientific-task performance under their stated comparisons. The laptop exercises do not reproduce their training or establish general RSI.
