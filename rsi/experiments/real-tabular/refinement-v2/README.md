# Make parameter changes survive composition

The first matched comparison exposed a concrete defect. A template changed
a tree's minimum leaf size, but a later capacity operator assigned the same
leaf size to every template. Two different source files constructed the same
estimator. The completed experiment is preserved.

This version refines each template's own settings. For the observed factor
0.3 case, the base tree's leaf size becomes three and the leaf-two template's
becomes seven. The earlier implementation assigned ten to both. Histogram
leaf count and regularization also retain their template references.

A second source review found a related problem: the old “higher capacity”
branch capped an unlimited tree's depth at 24. The current builder preserves
unlimited depth for factors above one. If no other setting changes, the
candidate is a duplicate and the constructor guard can refuse it before a fit.

## What the guard means

`admit_distinct` inspects a bounded list supplied by the caller. It returns
accepted and refused proposals; it does not train, replenish the list or
grant extra attempts. The signature includes nested preprocessing, learner
settings and target transforms within the frozen builder and environment.

Some continuous parameters need a common numeric representation: `C=1` and
`C=1.0` specify the same kernel setting. Other numeric types are meaningful:
`min_samples_leaf=1` means one row, while `1.0` means the whole training-set
fraction. The guard preserves that distinction. It is a constructor identity
check, not a general proof that two arbitrary programs behave equivalently.

## Inspect the checked repair

The [repair evidence](../../../evidence/2026-09-22/composition-repair/README.md)
contains the failed first identity check, the corrected construction checks,
four actual integration fits and the final capacity review. The two known
tasks show a tie and a small regression. That tests execution; it does not
establish an effective research procedure.

```text
Read rsi/experiments/real-tabular/refinement-v2/README.md.
Show the original cancellation and the corrected tree settings.
Explain why an unlimited tree cannot become deeper.
Inspect both duplicate refusals and the integer/fraction counterexample.
Trace the four recorded fits to their exact builder sources.
Explain which changes affect construction, predictions and quality.
Keep the archived comparison unchanged. Do not start new fits.
```

The agent prepares code and commands. The [four-fit protocol](../../../../how-did-i-generate-it/rsi/validation/COMPOSITION-REPAIR-PROTOCOL.md)
is exhausted in the recorded execution. A reproduction needs its own declared
workspace and allowance. No final-evaluation data were used for these fits.
The later no-fit capacity correction preserves the exact constructors used
by both revised factor-0.3 integration fits; the source versions stay separate.

Next, test a revised allocation procedure against the strong fixed portfolio
on newly declared tasks. Removing duplicate work does not guarantee a better
choice of experiments.
