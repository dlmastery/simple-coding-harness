# Start from the archive in a fresh learner workspace

The advanced nested-study prompt now works without the author's live workspace.
It explicitly opens the completed archive and writes reports to a new sibling
folder. The diagnostic accepts an absolute output path and refuses an existing
folder. The original archived diagnostic and its outputs remain unchanged.

The [protocol](PROTOCOL.md) allows one diagnostic and two refusal probes, with
zero fits. See [commands](COMMANDS.md), [actual output](DIAGNOSTIC-OUTPUT.txt),
[entry checks](ENTRY-CHECKS.txt) and [manifest](MANIFEST.csv). Fourteen original
workspace files were copied with matching byte hashes before adding this page.

## What actually ran

The diagnostic passed **133 checks against 39 archived inputs**. Its three CSV
outputs match the earlier diagnosis byte for byte. The existing-folder probe
exited 1, the relative-path probe exited 2, and the reports stayed unchanged.
These are meaningful refusal checks, not ignored failures. The reports contain
twelve comparisons: I0 and I1 against the parent on six tasks.

The [source trace](INHERITED-SOURCE-TRACE.csv) checks three cases. I1's retained
generation-one researcher matches the parent bytes of generation two. That
second researcher's hash matches the source and all twelve ledger entries on
each inspected task. The chosen candidate also matches the recorded choice.
The [trace script](trace-inheritance.ps1) and [output](INHERITANCE-OUTPUT.txt)
are retained. This checks recorded lineage within the local trust boundary;
it does not prove independent LLM behavior or a security boundary.

## Follow three outcomes

| Case | What the archived comparison shows | What to learn |
|---|---|---|
| Spam, task 43 | I1 improves aggregate balanced accuracy; 15 of 800 predictions change. Its winner is the common fourth probe. | A changed search can select a different existing candidate. The winner need not be a newly invented model. |
| DNA, task 45 | The selected constructors differ, but all 622 class predictions match. | Different code can produce an exact predictive tie. This is not a small gain hidden by rounding. |
| Miami housing, task 361260 | All 800 predictions change. I1's selection loss improves, but final MAE worsens. | Selection improvement does not guarantee held-out benefit. |

[Three concrete prediction rows](PREDICTION-EXAMPLES.csv) expose another useful
limit. The first changed spam row becomes wrong even though aggregate balanced
accuracy improves. A method can gain overall and still harm individual cases.
The first housing example also worsens. The DNA row stays identical. These
rows were chosen by an explicit first-row rule, not sampled for representativeness.
Use the full prediction records and aggregate checks for the actual comparison.

## What remains untested

This was the maintainer following the revised student entry path in the same
host and agent context. Learner predictions and quiz answers are marked skipped.
It is neither a new training run nor an independent student reproduction.
No closed study was resumed, no evaluation data were used to tune a new method,
and no claim of an overall RSI quality gain changed.
