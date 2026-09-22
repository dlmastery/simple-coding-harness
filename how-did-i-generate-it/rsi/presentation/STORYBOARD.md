# RSI masterclass presentation source

Status: teaching sequence and speaker-note draft. The PPTX is pending the
experimental repair gates in the presentation brief. This file is authoring
provenance, not a finished presentation. Results placeholders below describe
required evidence; they must not appear in a delivered slide deck.

Audience: an advanced AI/ML class that knows training and evaluation but has
not studied RSI. Plan a 75–90 minute lecture with discussion, followed by the
separate codelabs. This is a planning estimate. The full course takes much
longer and has its own duration guidance.

Use a white canvas, dark navy text and restrained teal emphasis. Use the
existing professional illustrations at their natural proportions. Use one
main idea per slide. The filename under each visual refers to
`rsi/assets/illustrations/`. Keep charts and result tables editable in PowerPoint.
The final speaker notes must contain the full primary-source and evidence links.

## 01 · Recursive self-improvement in ML research

On slide: A course in changing models, research procedures and the procedures
that improve them.

Visual: `main-overview-v2.png`.

Speaker notes: Begin with a familiar question: how would you improve a model
that predicts hourly demand? Students will suggest better features or a
different model. Keep those suggestions. We will later ask how a system chooses
among them, and how it can improve that choice process. The picture introduces
different objects that can change. It does not report a measured result.

Source: course README and lab 09.01.

## 02 · Learning objectives

On slide: Explain each changed object. Run a bounded experiment. Verify later
use. Judge quality and cost on new work.

Visual: `course-mindmap-v2.png`, with the lecturer following the numbered route.

Speaker notes: The practical goal is to inspect an improvement claim without
relying on its label. By the end, students should identify the object that
changed, the evidence that motivated the change, and the later comparison that
tests it. Explain the course prerequisites and the difference between this
lecture's planning estimate and the longer, hands-on codelab route.

Source: START-HERE.md, COURSE-MAP.md and TEACHING-ROADMAP.md.

## 03 · The complete data-science task

On slide: Define the prediction. Inspect the data. Build a baseline. Diagnose
errors. Compare a change. Report what generalizes.

Visual: `data-science-process-v4.png`.

Speaker notes: RSI still depends on sound data science. A sophisticated
controller cannot rescue an invalid target or a leaking split. Follow one
row through this picture and ask when its target may influence a decision.
The core course uses bike-demand regression. The repaired research extension
also uses classification and controlled regression tasks.

Source: theme 00 and benchmark-repair protocol.

## 04 · Data available at prediction time

On slide: An input must exist when the prediction is made.

Visual: `target-leakage-v2.png`.

Speaker notes: The bike component counts sum to total demand. Giving both
components to the predictor reveals the answer. Ask students to identify the
shortcut before explaining it. Observed weather also changes the question:
retrospective demand estimation is different from forecasting tomorrow with
unknown weather. State the intended use before interpreting accuracy.

Source: lab 00.01 and the bike data card.

## 05 · Training, selection and final evaluation

On slide: Training fits parameters. Selection chooses among candidates. Final
evaluation tests the frozen choice.

Visual: `freeze-before-final-v2.png`.

Speaker notes: A final score stops being a clean test if we use it to choose
the next revision. This applies to whole procedures as well as individual
models. New rows test row generalization. New task instances test a broader
question, but new seeds from a known generator still do not establish transfer
to a new scientific domain. Our local filesystem boundary is procedural.

Source: theme 08 and discovery-evaluation protocol.

## 06 · A baseline with one learned number

On slide: A training-median predictor gives a simple reference for regression.

Visual: `training-median-baseline-v1.png`.

Speaker notes: Work through the small illustrated example before discussing
larger models. The predictor learns its constant from training rows. We then
measure error on different rows. A weak baseline helps teach the metric, but
an effectiveness study also needs strong baseline procedures. Beating the
training median does not by itself show that a research agent improved.

Source: lab 00.03 and the figure's illustrative-number caption.

## 07 · One model change

On slide: A hypothesis connects an observed error to a proposed experiment.

Visual: `one-factor-model-change-v1.png`.

Speaker notes: Ask students to name one change and what observation would
count against it. A record that says only “try a better model” gives little
insight into the decision. Keep the old prediction file. A failed candidate
is useful evidence when its assumptions and cost remain visible. At this
stage, the research procedure stays fixed.

Source: early experiment labs and run-ml-experiment skill.

## 08 · Skills, agents and tools

On slide: A skill supplies a procedure. An agent applies it. A tool executes an
operation. A checker examines the result.

Visual: `skill-agent-tool-check-v2.png`.

Speaker notes: Students give instructions in ordinary language. The coding
agent writes code and configuration. A Markdown file alone does not prove
that an agent followed it. Ask students to point to a decision in an execution
trace and the instruction that governed it. This distinction becomes central
when we claim that a revised skill helped later work.

Source: theme 01 and the shared course skills.

## 09 · A bounded improvement loop

On slide: Each attempt reads state, makes one decision and records an outcome.

Visual: `bounded-loop-v1.png`.

Speaker notes: A loop needs more than a repeat command. It needs a stopping
condition, a retained best result and a record of consumed resources. Ask what
happens if the process crashes just after a fit starts. Restarting the program
must not erase that attempt. Repetition under a fixed rule is useful automation;
we have not yet changed the improvement rule.

Source: theme 02.

## 10 · A graph of dependent work

On slide: A result depends on the correct data, code and earlier decisions.

Visual: `artifact-dependencies-v2.png`.

Speaker notes: A graph makes dependencies explicit. If an input changes,
some descendants need new evidence. A table that combines scores from different
datasets can look convincing while answering no valid comparison. Follow one
dependency and ask which hash or record establishes that it is the intended
input. Graph completeness also matters: an omitted edge can hide a requirement.

Source: theme 03 and graph-reconciliation evidence.

## 11 · Meaning and validity rules

On slide: An ontology names the objects and the relationships that must hold.

Visual: `graph-ontology-v1.png`.

Speaker notes: A workflow graph describes what depends on what. Domain rules
describe what those objects mean. A valid numerical score can still refer to
the wrong target, time period or unit. Ask students for a rule that software
can check directly and a rule that needs domain judgment. Do not equate adding
an ontology file with establishing the truth of every statement in it.

Source: theme 04.

## 12 · The complete research system

On slide: Reliable behavior depends on how the components work together.

Visual: `system-coordination-v3.png`.

Speaker notes: Improvements can come from coordination even when component
models stay fixed. A planner may request a candidate that a tool cannot build.
A checker may validate the wrong output. Trace one request across the system
and show the joins that keep its identity intact. Later, when components
change, we must retest their combined behavior.

Source: theme 05.

## 13 · A harness generated from a brief

On slide: A readable task brief guides the creation of an executable harness.

Visual: `meta-harness-v2.png`.

Speaker notes: The builder creates a harness for the requested task. The
generated code still needs execution checks. Distinguish a usable generated
artifact from a better builder. A builder that produces a second harness
under unchanged instructions has demonstrated reuse. Evidence that the builder
itself improved requires a comparison of builder versions under matched work.

Source: theme 06 and capstone-harness evidence.

## 14 · The meanings of self-*

On slide: The changed object determines the claim.

Visual: `self-star-v2.png`.

Speaker notes: Introduce reflection, organization, emergence, adaptation and
self-improvement as distinct questions. Researchers use these terms in
different ways, so keep the source's definition nearby. A changed assignment
of work does not establish changed model parameters. An unexpected pattern
does not establish that the system rewrote its improver. Ask students to name
an artifact that could support each label.

Source: theme 07 and glossary.

## 15 · Reflection as a testable hypothesis

On slide: A critique matters when it changes a checked decision.

Visual: `reflection-hypothesis-checks-v2.png`.

Speaker notes: A fluent critique can be wrong. Convert it into a proposed
change and a falsifying observation. Preserve the prediction made before the
experiment, then compare it with the outcome. The useful evidence is the
resulting behavior and its measurement, rather than how persuasive the critique
sounds. This keeps reflection connected to an external check.

Source: self-reflection lesson and scientific-claim evidence.

## 16 · Organization and emergent patterns

On slide: Shared rules can change coordination while the rules themselves stay fixed.

Visual: `organization-shared-queue-v1.png`.

Speaker notes: A shared queue can change which worker takes a task. That is
an organizational mechanism. Discuss how a new coordination pattern might
appear without a learned update. Ask whether the pattern improves useful
throughput after coordination overhead. A surprising behavior, a useful
behavior and a revised improvement process require different evidence.

Source: labs 07.05–07.06 and their scheduling evidence.

## 17 · Solver, improver and evaluator

On slide: The solver does the task. The improver changes its procedure. The
evaluator judges the resulting work.

Visual: `name-experiment-objects-v2.png`.

Speaker notes: Use one concrete ML search as the example. A model parameter
belongs to the solution. An experiment-allocation policy belongs to the
research procedure. A rule that chooses among revisions to that policy belongs
to the improver. The external comparison stays fixed while internal procedures
change. Otherwise a system can appear to improve by changing what counts as success.

Source: lab 09.01 and improve-research-skill skill.

## 18 · Evidence of recursive use

On slide: A later improvement round must use the revised improver.

Visual: `inherited-improver-v1.png`.

Speaker notes: Saving a revised file establishes that a proposal exists.
Loading it later establishes source use. A trace showing its rule governing
a different decision adds behavioral evidence. A fair comparison then asks
whether the resulting process improves new work. Keep these observations
separate. A short lineage can demonstrate the mechanism without establishing
sustained acceleration or broad autonomy.

Source: labs 09.03–09.06 and MetaSkill method audit.

## 19 · Why the original results were mostly zero

On slide: Similar recipe sets often produced the same best candidate. Some
reported efficiency wins still executed every fit.

Visual: editable table separating candidate coverage, actual fits and final quality.

Speaker notes: Explain the original failure directly. Reordering the same
small recipe set often leaves the winning model unchanged. Labeling later
fits as wasted does not mean the program avoided them. Small validation sets
also made policy changes fragile. These issues motivated a search-space pilot,
actual inherited workspaces, real stopping decisions and separate task-level
evaluation. Preserve the negative historical results.

Source: RSI-RESULTS-DIAGNOSIS-2026-09-22.md.

## 20 · A fair procedure comparison

On slide: Same tasks. Same allowed resources. Frozen procedures. Separate final rows.

Visual: `matched-search-budgets-v1.png`.

Speaker notes: Equal allowances do not require equal spending. A policy may
stop early, but the report must show the quality it gives up or preserves.
Include failures and development overhead. The current experiment reports
model-fit time separately from worker-process time because process startup
can dominate small laptop jobs. Unknown agent inference cost prevents a claim
about net total research cost.

Source: discovery-evaluation protocol and research-cost ledger.

## 21 · Research benchmark scale

On slide: Laptop lessons expose mechanisms. Research benchmarks demand broader
search, stronger baselines and separate evaluation.

Visual: an editable comparison table for the local study, RSI-Exam and MLE-bench.

Speaker notes: Give concrete scale without treating the benchmarks as a single
league table. RSI-Exam describes up to twelve hours per task with separate
hidden grading. MLE-bench recommends substantially larger resources than a
laptop, although some individual tasks are small. Explain which comparison
question each benchmark asks. A faster small pipeline search does not establish
that an agent can engineer a correct GPU kernel or solve a new research domain.

Source: ../research/2026-09-22-BENCHMARK-SCALE.md and its primary links. Identify
MLE-bench as an older foundation, separate from recent releases.
## 22 · The research studio

On slide: Each method changes a specific part of scientific work.

Visual: `research-studio-map-v3.png`.

Speaker notes: Use the map to locate the methods rather than asking students
to memorize all names. The important questions are what changes, what feedback
drives the change, and what later evidence supports it. The studio includes
source reading as well as experiments. A paper's reported result, a classroom
adaptation and an independent reproduction must remain distinct.

Source: theme 10 overview and research sweep.

## 23 · Dream-RSI: discovery history and replay

On slide: A recorded tree supports policy experiments without repeating every fit.

Visual: `replay-boundary-v2.png`.

Speaker notes: A policy can ask to start again from the root or continue an
observed leaf. Replay exposes the recorded continuation. It cannot supply a
score for an untried branch. In the laptop adaptation, the inner proposer is
a fixed program and the coding agent revises the exploration policy. Explain
this simplification before showing local results.

Source: Dream-RSI v1, https://arxiv.org/html/2609.14858v1, and online-discovery evidence.

## 24 · Deployment after replay

On slide: A selected policy needs a new online test.

Visual: `replay-to-online-v2.png`.

Speaker notes: The recorded worlds determine which counterfactual questions
replay can answer. Our development cycle promoted one revision, then retained
it in the next round. Later runs loaded its exact source and added new trees
to the history. That establishes the cycle's operation. The paired evaluation
is the separate test of whether the revised policy helps new task instances.

Source: online-discovery archive and POLICY-LINEAGE-CHECKS.csv.

## 25 · RSIAgent: exploration and actor memory

On slide: Checked outcomes inform memory that the actor uses during later work.

Visual: `actor-memory-v2.png`.

Speaker notes: The outcome verifier checks what happened. The actor decides
what lesson to retain. A correct score does not make every generalization from
it correct. Explain broad practice followed by focused investigation, then a
comparison with learning disabled. The paper includes target-conditioned
practice, so distinguish that setting from evaluation on new tasks. State the
actual context separation used in each local experiment.

Source: RSIAgent v1, https://arxiv.org/html/2609.15364v1, and repaired-method requirements.

## 26 · Recuris: working state and reusable experience

On slide: Current state supports this run. Retained experience can guide later runs.

Visual: `working-state-and-experience-v1.png`.

Speaker notes: A pending action and a reusable research lesson serve different
purposes. Mixing them can preserve obsolete state as if it were a general
rule. Ask students which record they would carry into a new task. A memory
change needs evidence, scope and later-use checks. Its value depends on the
retrieval and execution process, not simply on keeping more text.

Source: Recuris, https://arxiv.org/abs/2608.24876, and the course's method notes.

## 27 · AIDE2: improving the researcher

On slide: An outer process changes the harness that runs inner ML searches.

Visual: `nested-research-v2.png`.

Speaker notes: Draw attention to the unit of evaluation: an entire inner
search. Its proposal operators, context and parent selection affect what the
search can discover. Count the losing inner searches as part of the outer
cost. A changed harness must execute later searches under a fair comparison.
A rearranged list that still evaluates every recipe may leave quality unchanged.

Source: Weco report, https://www.weco.ai/blog/first-evidence-of-recursive-self-improvement,
and 2026-09-21-AIDE-METHOD-AUDIT.md. The report is an explicitly dated older foundation.

## 28 · Ignition is a separate test

On slide: A better inner researcher may still fail in the outer improvement role.

Visual: `ignition-role-transfer-v1.png`.

Speaker notes: Moving a discovered researcher into the role that improves
researchers changes the task. Success at model search does not guarantee
success at harness design. The source audit records that the reported ignition
efficiency difference was not statistically significant. Keep that outcome
distinct from the inner-researcher improvement and from evidence of sustained
recursive gains.

Source: Weco report and AIDE method audit above.

## 29 · MetaSkill: task skills and their updater

On slide: Fast updates change task skills. Slower updates change how those skills evolve.

Visual: `meta-skill-schedules-v3.png`.

Speaker notes: The source coordinates several meta-skill roles, including
analysis, retrieval, allocation, proposal and evolution. A later round must
use the revised updater, not merely store it beside the old one. State which
roles and branch mechanisms the local adaptation implements. The classroom
fixture and the paper's full system support different claims.

Source: MetaSkill-Evolve v1, https://arxiv.org/html/2607.05297v1, and its method audit.
This is an explicitly dated older foundation.

## 30 · ScientistTwo: a chain of scientific evidence

On slide: A scientific claim needs experiments, ablations and a response to criticism.

Visual: `scientific-claim-v2.png`.

Speaker notes: A plausible hypothesis is the start of a scientific process.
Ask which observation would distinguish its mechanism from a simpler
explanation. A review score supplies feedback, but its meaning depends on who
or what produced it. Distinguish automated review from publication acceptance
and independent replication. Connect each revised claim to the experiment
that changed the evidence.

Source: ScientistTwo, https://arxiv.org/abs/2609.19644, and scientist-method audit.

## 31 · ScienceBuddy: model and harness co-evolution

On slide: Human scientific feedback can inform both the harness and model training.

Visual: `model-harness-v4.png`.

Speaker notes: Changing instructions or tools and changing model weights are
different interventions. Their effects may interact. Explain the source's
human-grounded tasks and evaluation rubrics before describing coupled updates.
The laptop activities do not train a frontier model. Any paper-reported
accuracy figure must carry its exact benchmark, comparison and source in the
notes, separate from our measured classroom results.

Source: ScienceBuddy, https://arxiv.org/abs/2609.17523, and sciencebuddy-result-audit evidence.

## 32 · Repaired experimental results

Authoring requirement: use the final checked result table. Show task-level
quality and actual search cost separately. Include the original baseline,
greedy control, lineage-only control, evolved policy and stopping ablation.
The four-task shakedown is supporting evidence, never the final headline.

Speaker-note requirement: explain what changed in the procedure, how it was
selected, when it was frozen, and which uncertainty remains. Discuss predictive
ties directly. State whether a result supports quality, efficiency, both or
neither. Link the selected source, prediction checks and cost accounting.

## 33 · Evidence across the seven repaired comparisons

Authoring requirement: an editable table with separate columns for implemented
mechanism, later use, predictive outcome, resource outcome and remaining limits.
Populate only after each required method comparison has its reviewed evidence.
Do not turn one discovery-policy study into seven separately validated methods.

Speaker-note requirement: walk through one successful change and one rejected
or harmful change. Explain why a faithful mechanism can still fail to improve
the selected benchmark. Keep source-paper performance separate from local results.

## 34 · What the evidence supports

Visual: `evidence-beyond-score-v1.png`.

Speaker-note draft: A final score is one piece of evidence. Source identity,
observed later use and fair comparison answer different questions. Ask students
to state the strongest claim the current evidence supports, then identify the
additional experiment required for a stronger claim. The final slide text
must follow the reviewed outcomes rather than promise acceleration in advance.

## 35 · The capstone projects

On slide: Build a harness. Test a retained lineage. Check portability. Audit a claim.
Teach the evidence.

Visual: `capstone-map-v3.png`.

Speaker notes: The capstones combine the course's earlier distinctions.
Students should bring a traceable portfolio rather than only their best score.
A clear negative result can satisfy a scientific learning objective when the
question, experiment and interpretation are sound. That does not automatically
satisfy a product objective that requires an effective improver. Name the
criterion the capstone actually tests.

Source: theme 11 and the five capstone briefs.

## 36 · Laptop and cluster execution

On slide: More compute changes the scale. The comparison contract still governs the experiment.

Visual: `compute-contract-v2.png`.

Speaker notes: A larger cluster can support more expensive models or tasks.
Keep data roles, budgets, failure accounting and procedure freezes explicit.
Wall time and total compute can move in different directions under parallel
execution. A documented cluster adapter does not establish that we ran it.
State the tested backend and preserve untested capabilities as open work.

Source: scale-experiment skill and capstone-portability evidence.

## 37 · Discussion and next experiment

On slide: What changed? What proves later use? What would you test next?

Visual: `capstone-teach-back-v2.png`.

Speaker notes: Give students a concrete example: a system saves a new policy,
uses fewer fits on later tasks and reports tied final quality. Ask what that
supports and what it leaves unresolved. Then ask what extra evidence would
support improvement of the improver. Let students propose the next experiment
before showing the course's quiz explanations and teaching roadmap.

Source: glossary, capstone 11.05 and TEACHING-ROADMAP.md.

## Production checks still required

Before PPTX export, reconcile slides 19 and 21–34 with the finished experiment
records and current source audits. Complete every speaker note with its source
links. Import editable charts from checked CSV data. Render every slide, inspect
text size and illustration labels, check note parts inside the PPTX, and retain
the authoring source, assets and visual review in GitHub. The delivered deck
must contain no placeholder result slides or authoring-status comments.
