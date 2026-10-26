# A better search order is not yet a better improver

This author walkthrough covers [10.13](../../../10_research_studio/04_aide2/step_13_inner_research/README.md), [10.14](../../../10_research_studio/04_aide2/step_14_outer_research/README.md), and [10.15](../../../10_research_studio/04_aide2/step_15_ignition/README.md). It ran ten small regression fits and a separate set of no-fit decision fixtures. The existing lesson illustrations explain the mechanism; the files below provide the measurements.

## Follow one search

The fixed researcher proposes four candidates. Each non-baseline candidate starts from the retained recipe. A weaker candidate stays in the trace but does not become the next parent.

| Attempt | Operator | Recipe | Selection MAE | Decision |
|---|---|---|---:|---|
| 1 | Draft | Median baseline, calendar | 159.947912 | Retain |
| 2 | Refine | Linear, calendar | 109.807668 | Retain |
| 3 | Explore | Tree, calendar | 125.049488 | Reject |
| 4 | Enrich | Linear, calendar and weather | 99.175924 | Retain |

MAE measures rentals per hour; smaller is better. The fourth attempt changes the retained linear recipe, not the rejected tree. Open the [procedure](10-13/INNER-RESEARCHER.md), [before-action notes](10-13/before-04.md), [full trace](10-13/TRACE.csv), and [retained recipe](10-13/RETAINED.md). The [reordered replay](10-13/REPLAY.csv) reaches tree/all, an unobserved recipe in this search, and stops with unknown. It performs no new fits.

## Change the procedure, then compare it

The [outer proposal](OUTER-PROPOSAL.md) moves enrich before explore. Both frozen procedures then start empty and receive three fits. The earlier four-fit search motivates the change; it is not reused as the parent comparison arm.

| Researcher | First three operators | Retained selection MAE | Fits |
|---|---|---:|---:|
| R0 | Draft, refine, explore | 109.807668 | 3 |
| R1 | Draft, refine, enrich | 99.175924 | 3 |

Read the [comparison](10-14/COMPARISON.csv), [R0 trace](10-14/R0/TRACE.csv), [R1 trace](10-14/R1/TRACE.csv), and [frozen identities](COMPARISON-FREEZE.csv). R1 reaches the useful feature change sooner. This is a selection-data result on a previously exposed task. The [unequal-budget illustration](10-14/UNEQUAL-BUDGET.md) is unexecuted and contains no invented score.

## Ask a different question about the improver

The [shared role adapter](ROLE-ADAPTER.md) projects each frozen researcher's third operator preference into the same target procedure. This is a deliberately narrow mechanical proposal, not general researcher-code generation. The [two produced proposals](10-15/PROPOSALS.csv) are evaluated by executing the affected decision on the same three fixtures.

R0 repeats a recipe in one case; R1 repeats one in the other. Both stop when the budget is empty. Each passes two of three behavior cases. The [six recorded outcomes](10-15/FIXTURES.csv) contain no model-quality scores. The [separate overcomplication check](10-15/OVERCOMPLICATION.md) refuses five branches when only one slot remains. There are no model fits in these checks.

This result cannot establish ignition. The earlier task-search win does not answer whether R1 can generate better researchers. Read the [claim audit](CLAIM-AUDIT.md) and [selected primary-source reading](SOURCE-AUDIT.md) for the distinction and the missing evidence.

## Inspect the boundary and cost

The [data inspection](data-inspection/DATA-REPORT.md) found 17,379 rows, no missing cells, and no exact duplicates. It also printed public final-partition aggregates. The original protocol's instruction not to access final data was too broad; [the exposure note](EXPOSURE-NOTE.md) records that correction before the outer comparison. No final model evaluation occurred. These public data were not blinded.

All ten fits passed the supplied separate prediction check. Their total recorded fit time was 0.763555 seconds. Inspection, fits, and checks took 33.770220 seconds across 21 subprocess commands; fit time is already included in that total. [Cost accounting](COST.md) keeps unknown author and provider costs explicit. There was no learner assessment, independent coding-agent comparison, paper reproduction, GPU run, or cluster run.

The [manifest](MANIFEST.csv) covers 142 original files. Copies were checked against their original SHA-256 hashes. The manifest itself and this archive guide are publication additions outside that file list. The original protocol, its corrected copy, all procedures, source snapshots, decisions, checks, and rejected outcomes remain available. Start a new sibling workspace to run your own lab; do not edit this archive.
