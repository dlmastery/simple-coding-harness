# What changed after the zero-gain results

[Course](README.md) · [Measured examples](evidence/README.md) · [Research studio](10_research_studio/README.md)

The original concern was right: a table of zeros did not demonstrate a better
researcher. The repair now separates three questions:

1. Did the model's predictions improve?
2. Did the research procedure use fewer actual experiments?
3. Did changing the improver produce better researchers later?

These questions need different comparisons. A method can answer one positively
and leave another unresolved.

## Why a search can change while its best score stays the same

Imagine two students trying the same 24 recipes. One finds the best recipe
first; the other finds it last. If both still run every recipe, their final
best score and total fit count can be identical.

That was a central weakness of the original interface. Its win rule also
allowed equal predictive quality with fewer “wasted fits.” Earlier discovery
can be useful, but it is not automatically a reduction in executed work.
The [original diagnosis](../how-did-i-generate-it/rsi/validation/RSI-RESULTS-DIAGNOSIS-2026-09-22.md)
distinguishes the inspected contracts from the user's historical result table.

The corrected comparisons limit search below the available candidate space,
allow new parameterized pipelines, preserve strong conventional controls and
record actual worker executions. A changed name or source file is not enough:
composed operators can still construct the same model. The
[operator repair](evidence/2026-09-22/composition-repair/README.md) checks that
case and preserves the failed versions.

## Search efficiency: a measured improvement with a limit

![A recorded policy is checked in replay and then used in a new online discovery run.](assets/illustrations/replay-to-online-v2.png)

*Conceptual mechanism. The counts below come from actual execution records.*

The completed Dream-inspired comparison used **55 search fits** with the
replay-selected policy, compared with **192** for broad search. Broad search
with the same stopping threshold used **84**. The stopping control matters:
some savings come from stopping, not from a better exploration policy.

Against broad search, predictive quality improved on three tasks, tied on
twelve and worsened on one. Its paired uncertainty interval includes zero.
This supports lower measured search work in this setting; it does not establish
a predictive gain or lower total research cost after development and agent
inference. These were new instances of known synthetic task families.

Read the [sixteen-task results](evidence/2026-09-22/discovery-final/README.md)
and [online policy lineage](evidence/2026-09-22/online-discovery/README.md).
The local proposer is a fixed program, not a full reproduction of Dream-RSI.

## Researcher improvement: evaluate the whole search

![An outer procedure revises a researcher, whose complete inner search is then evaluated.](assets/illustrations/nested-research-v2.png)

*The researcher is the unit being revised. Its individual models are the work
it performs. The outer comparison must pay for unsuccessful searches too.*

The first public-data comparison showed why a strong control is essential:
retained experience beat random search but lost to a sensible fixed portfolio
overall. The changed updater had mixed results. Those
[324 attempts](evidence/2026-09-22/tabular-comparison/README.md) remain visible.

The next study generates complete executable researchers. Each runs twelve
model attempts and chooses later experiments from observed feedback. A simple
improver, I0, changes its local refinement schedule. The revised improver, I1,
changes how it preserves coverage, tests alternatives and chooses model parents.
Both are bounded programs written by the coding agent.

On six previously exposed development tasks, I1's researcher improved two
evaluation results and tied four. Its mean normalized loss change, −0.002142,
narrowly passed the predefined −0.002 gate. The interval reaches zero. I0 tied
all six and its child was rejected. These are
[small development gains](evidence/2026-09-22/nested-research-development/README.md),
not fresh transfer evidence.

## Where the recursive part must appear

Saving I1 does not prove that it was used. The trace must show I1 governing a
later researcher revision and that new researcher executing another search.

After the development verdict, both frozen improvers were invoked again.
I1 inherited its promoted researcher; I0 inherited the original parent.
They generated second researchers from those parents and the completed traces.
Their [parent and improver identities were checked](evidence/2026-09-22/nested-research-development/GENERATION-CHECKS.csv).

The resulting researchers have now run on six reserved datasets against the
parent, fixed portfolio and random search. All 360 searches completed before
thirty globally frozen choices were scored. The final audit passed 10,813
checks. The full development and evaluation study used 624 model attempts.

I1 improves two tasks, ties three and worsens one against I0 and the parent.
Its mean normalized loss change is +0.000120, with an exploratory interval
of [−0.001826, +0.002390]. This does not establish an overall quality gain.
Against fixed search its mean is better, but that interval also includes zero.
Against random search its mean is worse. All controls belong in the conclusion.

![Actual final scores for the parent, fixed and random controls, and researchers generated by I0 and I1.](evidence/2026-09-22/nested-research-evaluation/native-scores.png)

*[Read the complete reserved-task comparison](evidence/2026-09-22/nested-research-evaluation/README.md),
including native metrics, uncertainty, source inheritance and all costs.*

This establishes neither autonomous invention nor sustained acceleration.
The coding agent supplied the updater revision, the rewrite space is bounded,
and the host shares access to all files. The changed improver did produce and
execute a later researcher, but its overall benefit remains unestablished
under this contract.

## Read a result without mixing its claims

| Observation | What it supports | What it does not establish |
|---|---|---|
| A new source hash | A file changed | Behavior changed |
| Different executed model choices | The researcher behaved differently | Better predictions |
| Fewer actual fit attempts | Less executed search work | Lower total research cost |
| A child passes its development gate | It met that declared selection rule | Fresh-task transfer |
| A revised improver governs a later search | Later use of the revised procedure | General superiority or acceleration |

All selected outcomes, failures, sources and known costs belong in the report.
One good task should not replace the whole comparison. Use the
[recursive capstones](11_capstones/README.md) to practice making that argument,
then explain both a successful change and a retained parent.
