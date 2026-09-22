# The next comparison must test procedures, not a reordered full grid

Development is closed: 96 attempts, all retained, across six tasks. The
second revision improved the two digit tasks' selection scores. No new
regression proposal beat its incumbent. Three replay weights tied; the
declared rule retained the simplest, alpha zero. These findings determine
the next implementation. They do not establish task-transfer gains.

This is an implementation design, **not yet a frozen execution protocol**.
Finish the runner, inspect its mechanisms and budgets, and freeze exact
sources before any reserved-task fitting. Do not run another development
batch. Do not silently add tasks after seeing their results.

## Six procedures, distinct comparisons

Use reserved tasks 6, 23, 31, 361235, 361237 and 361247. Every procedure starts
from the same copied training/selection rows, seed 41 and four broad probes.
The classifier probes linear, Extra Trees, RBF C=1 and histogram boosting.
The regressor probes the median, linear, random forest and RBF C=1.
Each procedure has eight total admitted fits and a 30-second subprocess limit
per fit. Failures consume slots. Every fit actually runs; no shared result
cache may be reported as saved training. Final scoring follows a global
choice freeze and charges at most one refit per selected procedure/task.

| Procedure | Last four actions | Question |
|---|---|---|
| Fixed portfolio | Complete the conventional diverse portfolio, with the regression median included | How strong is ordinary model selection? |
| Random search | Use a fixed seeded sampler over the available builders and bounded hyperparameters | Does retained experience beat a conventional search control? |
| Frozen experience | Read the checked global-rank memory and execute its next four untried candidates | Does the retained task skill help on different tasks? |
| Parent updater and parent harness | Generate two local refinements, retain the incumbent or a child, then generate two further refinements | What does sound feedback-driven local search achieve? |
| Parent updater and revised harness | Use the same updater, with the source-level representation/objective operators added during development | Does the changed harness help under the same controller? |
| Revised updater and revised harness | Use the revised five-role updater to generate and then revise a research skill across two later rounds | Does changing the updater help beyond changing its harness? |

Eight fits must be fewer than the useful proposal space. The local refinements
and random control must generate actual new parameterized candidates, not
simply exhaust the 16 recorded development points. Each proposal keeps its
parent, source, parameters, reason, admission and outcome. Candidate selection
and child-workspace inheritance must be observable in the recorded trace.

The fixed portfolio and random sampler are controls, not deliberately broken
procedures. Both use training-only preprocessing, metric-correct selection,
sound category handling and the median reference. The random control gets the
revised builder space too. It cannot be restricted to the older weaker space.

## What the updater changes

The parent updater is a conventional local optimizer: inspect current
selection feedback, select the incumbent, allocate two refinements, propose
bounded parameter changes, and retain only a checked improvement. It must not
rank by training error or invent conversions to make the child win.

The revised updater is authored from the accumulated development failures.
It reads five versioned role instructions: Analyzer, Retriever, Allocator,
Proposer and Evolver. It distinguishes a missing reference, overfitting and a
representation question; retrieves scoped checked experience; divides each
two-fit round between an evidence-guided alternative and local refinement;
and preserves the incumbent when the candidate loses. Later proposal source
and decisions must identify the exact inherited updater and role-file hashes.

Both updaters produce a research-skill artifact after the four probes. Its
first two candidates actually run. A later skill revision is produced from
that feedback and governs the final two fits. This creates inspectable later
use of the changed updater. Merely saving five Markdown files is insufficient.
Any internal acceptance decision must precede the next use. The external
metric and final evaluator stay identical across the comparison.

The root coding agent authors these revisions. The inner executable proposer
is a bounded program, not an independent LLM researcher. Five role files do
not imply five independent agents or a model-weight update. Preserve these
limits in the report and slides.

## How this addresses the original seven rows

- Proof and the meta gate become shared checked invariants. Their presence
  is not advertised as a separately measured accuracy intervention.
- Dream-style tree/replay/renewed-discovery evidence remains in the completed
  earlier study. The new 144-lookup finite-candidate replay is an additional
  control; it does not replace that mechanism with a renamed ranking list.
- Memory and exploration lessons connect outcome verification, actor-authored
  persistent memory and later frozen-memory use. Keep current run state apart.
- The parent/revised harness pair addresses researcher implementation changes.
- The parent/revised updater pair addresses later use and effectiveness of an
  inherited improver. Preserve the distinction from changing only task skills.

Do not label these rows reproductions of Recuris, RSIAgent, AIDE2 or
MetaSkill-Evolve. Map each preserved mechanism and each omission explicitly.
The existing source-specific codelabs still teach their distinct algorithms.
Combine their execution evidence with this fair ML comparison rather than
inventing a separate positive headline for every paper name.

## Results and completion

Freeze the six procedures, builder sources, role files, memory, data identities,
metrics, tie rule and budgets before fitting. Record all six-by-six outcomes,
actual training costs, failed proposals and final uncertainty. Use selection
feedback only during search. Do not reopen choices after final scoring.
Inference and complete research cost remain unknown unless measured.

The panel is small and public. This is a laptop method study, not official
OpenML evaluation, an industry-scale benchmark or proof of general RSI.
Its result may support a predictive gain, search benefit, regression or no
established advantage. Update the relevant skills, lessons, capstone evidence
and presentation from the actual result. The requested PPTX with notes remains
part of the final deliverable, after the method work and evidence review.
