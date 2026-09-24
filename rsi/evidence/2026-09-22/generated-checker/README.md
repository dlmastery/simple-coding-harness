# A generated checker catches a substituted row

Lab [01.04](../../../01_process_without_loops/step_04_separate_the_check/README.md) asks the coding agent to generate a separate checker. The earlier walkthrough reused the supplied implementation. This two-check author run closes that specific gap without another model fit.

The [generated checker](checker.py) accepts 4,358 saved selection predictions and recomputes MAE 159.94791188618632. In a copy, source ID 8645 becomes training-row ID 0. The same checker refuses the copy with exit status 2. [Only that cell changed](ONE-CELL-DIFF.csv).

Read the [report and limits](CHECK-REPORT.md), [declared protocol](PROTOCOL.md), [exact commands](COMMANDS.md), [passing output](valid-output.txt), and [refusal](substituted-output.txt). The [source identities](SOURCE-IDENTITIES.csv) record five unchanged copied inputs. Source data is the existing [pinned bike CSV](../../../examples/bike-demand/source/hour.csv).

The checker uses Python's standard library and does not import the course solver or supplied checker. Separate implementation in the same author context does not establish an inaccessible evaluator or authenticated model provenance. Learner responses remain unattempted. The additional-change explanation addresses what cannot be checked from a metric alone.

The [manifest](MANIFEST.csv) seals sixteen original files. This navigation page was added afterward. No original run files were normalized or rewritten for publication.
