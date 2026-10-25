# Explain order through required artifacts

| Predecessor | Required artifact | Dependent action |
|---|---|---|
| Frame | TASK.md: target, permitted inputs and metric | Inspect |
| Inspect | DATA-REPORT.md: quality, time coverage and repeated observations | Split |
| Split | Row identities for each partition | Fit |
| Fit | predictions.csv | Check |
| Check | CHECK.md: prediction and score verdict | Report |

The preserved workflow.mmd and workflow.png show these edges. Each edge names one requirement, not all inputs to its destination. Fitting also needs source data and a recipe; checking also needs trusted row membership and targets.

The normal ordering passes. Checking before fitting is refused because fit → check is violated. Splitting before inspection is refused under the original graph, but passes when inspect → split is removed. That final pass means the order respects an incomplete graph. It does not mean the split is scientifically justified: the designer can miss time coverage, duplicate observations or a quality problem that inspection should reveal.

The generated checker evaluates four declared complete permutations in an empty symbolic execution state. It does not run the ML nodes or certify arbitrary graphs. Existing files cannot satisfy a missing predecessor in this symbolic check.
