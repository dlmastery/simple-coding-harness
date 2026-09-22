# Change what the inner researcher can build

A search policy chooses where to spend the next attempt. An inner harness also
defines what that attempt can build. If every reachable pipeline misses an
important pattern, a better search order may only find the same inadequate
models faster.

This extension tests one code-level harness revision. The parent can build raw,
pairwise and quadratic features. The child adds a smooth spline basis to the
quadratic linear-model branch. Both retain the same broad-search policy and
attempt allowance. The coding agent writes the revision; students explain the
hypothesis, inspect the evidence and judge the result.

## Connect the idea to the course

Start after [the inner-research lesson](../../10_research_studio/04_aide2/step_13_inner_research/README.md)
and [the discovery-cycle extension](../tabular-discovery/README.md).
The [AIDE2 studio](../../10_research_studio/04_aide2/README.md) explains the
outer/inner distinction and the stronger, separate question of ignition.
Use its existing infographic to locate the change:

![An outer researcher changes an inner research harness, then evaluates what that harness can improve.](../../assets/illustrations/nested-research-v2.png)

This is an AIDE-inspired laptop adaptation. The inner proposer is a deterministic
program. One coding agent authors the outer change and checks the experiment;
role names do not create independent agents. A retained builder change does
not show that the procedure which proposes builder changes became better.

## Why these features?

Imagine a target that bends smoothly with one input and also depends on the
product of two inputs. Quadratic features can represent the product. A small
smooth basis can approximate the bend. The combined basis gives a regularized
linear model access to both patterns.

The proposal follows earlier development evidence and the known synthetic
generator. It does not infer an unknown law from an unseen industrial task.
The builder fits its imputer, scaling and basis on training rows only. It never
receives latent coefficients or the identity of the true signal features.
All ten inputs receive the same candidate transformation.

The child changes two related pieces: the builder adds a capability, and the
proposer schedules that capability within the existing twelve-attempt budget.
It tries the existing quadratic candidate one step earlier, replacing one
pairwise regularization probe. This can help or hurt. The comparison tests the
combined harness revision; it does not isolate those two edits from each other.

The [completed development comparison](../../evidence/2026-09-22/harness-revision-development/README.md)
ran 144 fits. Two tasks improved and four tied, but the mean gain did not meet
the original promotion threshold. The parent was retained and the conditional
final study did not run. Keep this result when deciding what to try next.

## Inspect it with your coding agent

Open the repository root and use this prompt. The inspection needs no model
fits and does not consume a lesson's training budget.

```text
Read rsi/experiments/harness-revision/README.md and CHANGE-PROPOSAL.md.
Compare its engine.py and proposer.py with rsi/experiments/tabular-discovery.
Explain one parent pipeline and the proposed child pipeline in plain language.
Show which inherited files let a later candidate run the changed builder.
Ask me to predict where the change will help and where it may overfit.
Do not run the maintainer study or claim a result from source inspection.
```

Then inspect the [development protocol](../../../how-did-i-generate-it/rsi/validation/HARNESS-REVISION-DEVELOPMENT-PROTOCOL.md).
It allocates six paired tasks and at most 144 attempts. This is a separately
budgeted maintainer study, not permission to exceed an individual lesson's
smaller allowance. Every candidate uses a real copied parent workspace.

The [conditional final protocol](../../../how-did-i-generate-it/rsi/validation/HARNESS-REVISION-FINAL-PROTOCOL.md)
uses twelve new instances only if the original development gate passes.
Choices must freeze before final scoring. Both protocols, sources and failures
remain available even if the revision is rejected.

## What to check

Look for the source freeze, actual parent and child workspaces, candidate
predictions, complete result tables and the gate decision. Check that
`parent_engine.py` travels with every child workspace: a hash of only
`candidate.py` would miss a changed imported builder. Inspect raw predictive
metrics separately from attempts and worker time.

If a worker fails, retain the attempt and its error. Do not increase its budget
or alter frozen code in place. If the gate fails, retain the parent. A new idea
requires a new declared development experiment; exposed final tasks cannot
become a tuning loop.

## Key takeaways

- Search order and the set of buildable pipelines are different intervention points.
- A real harness revision must reach the files used by later candidate processes.
- Richer features can improve fit and increase overfitting; check new tasks.
- An outer code edit can improve an inner researcher without improving the updater.

## Check your understanding

1. Both versions make twelve attempts. Can one still be a better researcher?
2. A child imports a revised builder, but its candidate file is unchanged.
   Is the candidate's file hash sufficient to identify its behavior?
3. The child wins the development gate. Can we call its selection score a
   final transfer result?

<details>
<summary>Compare your reasoning</summary>

1. Yes. Its attempts may produce better models. Compare final predictions
   and costs on the same new tasks; equal attempt counts do not imply equal quality.
2. No. Retain and check the complete executable dependency set and configuration.
3. No. Development determined which revision continued. A separate frozen
   comparison is needed, and even that has a stated task-distribution limit.

</details>

## What's next

Ask whether the retained procedure for proposing and checking harness revisions
can itself improve. Continue to [the ignition lesson](../../10_research_studio/04_aide2/step_15_ignition/README.md)
and [meta-skill evolution](../../10_research_studio/05_meta_skill_evolution/README.md).
Keep the changed object, later use and external comparison explicit at each level.
