# Twelve public tasks with explicit data boundaries

The panel contains six classification and six regression problems, selected
from metadata before training. Six are for procedure development; six remain
reserved for later comparison. See the exact roles, sizes, missing-value
counts and duplicate groups in [the panel](DATASET-PANEL.csv).

All **1,178 data checks pass**. No model was fitted during preparation.
The archive preserves 142 original files with matching bytes. Its
[manifest](ARCHIVE-MANIFEST.csv) includes raw ARFF data, exclusions, schemas,
group identities, row assignments, partitions, sources and audit results.
The earlier preparation manifest predates the later audit outputs.

## What the rows mean

| Task | Question | Source character | Role |
|---|---|---|---|
| 3, chess | Can White win this endgame? | Described game positions | Development |
| 6, letters | Which of 26 letters is represented? | Engineered letter-image measurements | Later comparison |
| 16, multiple features | Which digit is represented? | Karhunen coefficients from character images | Development |
| 23, contraceptive method | Which method does this survey record report? | Survey observations; association, not a causal or clinical recommendation | Later comparison |
| 28, optical digits | Which handwritten digit is represented? | Image measurements; prior course overlap | Development |
| 31, German credit | Which historical credit-risk label is recorded? | Historical credit records; teaching data, not a deployment claim | Later comparison |
| 361234, abalone | How many shell rings are present? | Physical specimen measurements | Development |
| 361235, airfoil | What is the sound-pressure level? | Controlled wind-tunnel measurements | Later comparison |
| 361236, auction | How long does property verification take? | Simulated auction configurations | Development |
| 361237, concrete | What is the compressive strength? | Mixture, age and strength measurements | Later comparison |
| 361244, solar flare | How many C-class flares follow? | Active-region observations | Development |
| 361247, naval propulsion | What is the compressor degradation coefficient? | Simulator output | Later comparison |

The exact OpenML versions, source URLs, raw hashes and licenses are in each
task's `SOURCE.md`. [The metadata archive and source review](../real-tabular-inventory/REVIEW.md)
preserve original descriptions and classification attribution. Its saved
OpenML descriptors link the regression sources and papers. These public
benchmarks include simulations; “public data” does not mean every row is an
observation from a deployed system.

## What changed, and why it matters

- The auction loader excludes `verification.result`, as the source requires.
  Its target is verification time. The failed first preparation remains
  [available](../real-tabular-data-v1/README.md).
- The [original chess file](original-chess/REVIEW.md) matches OpenML's row
  multiset exactly: 36 inputs plus the target. The website's 35-feature
  summary does not justify deleting a real input.
- [All 1,797 earlier scikit-learn digits rows overlap](DIGITS-EXPOSURE.md).
  Optical digits cannot be described as a new transfer task.
- Identical feature rows stay together. Solar flare has 822 repeated-input
  rows and 74 feature groups with different targets. CMC has 62 conflicting
  groups; concrete has nine. Identical observed inputs need not determine
  the answer, so some errors may be irreducible with these features.

The [declared preparation protocol](../../../../how-did-i-generate-it/rsi/validation/REAL-TABULAR-DATA-PROTOCOL.md)
uses deterministic grouped 60/20/20 partitions, capped at 2,400 training and
800 selection/final rows. This is a classroom adaptation, not the suites'
official cross-validation or the original digits writer split. Feature-group
isolation does not establish person, writer, site, region or temporal
independence where those identities are absent. Local final files are public
and procedurally withheld, not protected by a secure evaluator.

Next: run the separately declared development portfolio, then freeze each
improvement method and comparison before using the six reserved tasks.
