# Author execution evidence

Date: 20 September 2026. Host: Windows AMD64; Python 3.12.12. Package versions are in the [environment record](../../../how-did-i-generate-it/rsi/validation/foundation-environment.txt).

The maintainer agent ran the supplied data inspection and five ML fits. These are executed measurements. No student participated, so prediction checkpoints, quiz responses, and teaching effectiveness were not tested. No native Claude or Gemini session, GPU, or cluster run was performed.

| Task | Candidate | Selection metric | Local fit seconds |
|---|---|---:|---:|
| Bike | Training median | MAE 159.947912 | 0.070844 |
| Bike | Linear, calendar fields | MAE 109.807668 | 0.075903 |
| Bike | Tree, calendar and weather | MAE 115.284257 | 0.096247 |
| Wine | Majority class | Balanced accuracy 0.500000 | 0.047448 |
| Wine | Balanced logistic model | Balanced accuracy 0.744955 | 0.048011 |

The tree comparison changes both model and feature group, so it cannot isolate either factor's effect. These preliminary runs check execution; the loop lesson adds controlled comparisons. Times exclude process startup, data inspection, plotting, and agent inference. The host's memory and hardware are not a validation of an 8 GB laptop requirement. Peak memory was not measured.

The actual bike table has 17,379 rows. Its fixed partitions have 8,645, 4,358, and 4,376 rows. Rental demand grows across periods. This helps explain why an old training median has large errors on later data.

The red wine table has 1,599 rows, with 240 repeated input vectors. Group-based partitions have 978, 319, and 302 rows. Both classes occur in each. The baseline's ordinary accuracy would hide poor minority recall; balanced accuracy exposes it.

Inspect the complete [bike report](author-bike/DATA-REPORT.md), [bike comparison](author-bike/COMPARISON.md), and [wine report](author-wine/DATA-REPORT.md). Candidate directories retain hypotheses, predictions, measured results, and error slices. The data-overview plots were rendered and the bike plot was visually inspected.

Eight behavioral runtime tests passed. The legacy suite passed its offline checks and skipped 19 live checks. Those legacy tests do not establish that the rebuilt lessons work in another agent.

These measurements are public teaching evidence, not independent RSI results. No final partition was used for model selection during these fits. The public inspection report includes partition summaries and is not a secret holdout.

## Controlled walkthroughs

The [controlled walkthrough](walkthrough/README.md) adds nine actual fits and one final refit. It isolates a model change from a feature change, executes a bounded search, checks classification, rejects three domain contradictions, and verifies the final-evaluation lock. Adding weather to the same linear model changes selection MAE from 109.807668 to 99.175924. Replacing the calendar linear model with a calendar tree changes it to 125.049488: that proposal loses.

The [inheritance walkthrough](inherited-improver/README.md) retains two improver versions and an [executed trace](inherited-improver/EXECUTION-TRACE.md). The selected revised procedure requires a prediction-based check before promotion. It rejects a deliberately false report and retains a valid lower-error result. This demonstrates execution of an inherited instruction in an author-guided round. It does not establish autonomous revision, independent contexts, a general performance advantage, or recursive acceleration.

The shared suite now passes 15 tests. These checks and the synthetic mechanism fixtures cover specific paths; they do not mean all 101 learner activities or all coding-agent adapters have been executed.
