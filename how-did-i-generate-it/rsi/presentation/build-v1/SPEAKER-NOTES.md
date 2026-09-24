# 01 · Recursive self-improvement in ML research

Teaching point: A course in changing models, research procedures and the procedures that improve them.

Begin with a familiar question: how would you improve a model
that predicts hourly demand? Students will suggest better features or a
different model. Keep those suggestions. We will later ask how a system chooses
among them, and how it can improve that choice process. The picture introduces
different objects that can change. It does not report a measured result.

Source: course README and lab 09.01.

Course evidence and reading:
https://github.com/dlmastery/simple-coding-harness/blob/7db77bd8d38aa5f23dc4180e341de415d6b99296/rsi/README.md
https://github.com/dlmastery/simple-coding-harness/blob/7db77bd8d38aa5f23dc4180e341de415d6b99296/rsi/09_recursive_self_improvement/step_01_three_objects/README.md

Illustration: https://github.com/dlmastery/simple-coding-harness/blob/7db77bd8d38aa5f23dc4180e341de415d6b99296/rsi/assets/illustrations/main-overview-v2.png
The figure explains a mechanism. Its illustrative cards do not establish an empirical result.

# 02 · Learning objectives

Teaching point: Explain each changed object. Run a bounded experiment. Verify later use. Judge quality and cost on new work.

The practical goal is to inspect an improvement claim without
relying on its label. By the end, students should identify the object that
changed, the evidence that motivated the change, and the later comparison that
tests it. Explain the course prerequisites and the difference between this
lecture's planning estimate and the longer, hands-on codelab route.

Source: START-HERE.md, COURSE-MAP.md and TEACHING-ROADMAP.md.

Course evidence and reading:
https://github.com/dlmastery/simple-coding-harness/blob/7db77bd8d38aa5f23dc4180e341de415d6b99296/rsi/START-HERE.md
https://github.com/dlmastery/simple-coding-harness/blob/7db77bd8d38aa5f23dc4180e341de415d6b99296/rsi/COURSE-MAP.md
https://github.com/dlmastery/simple-coding-harness/blob/7db77bd8d38aa5f23dc4180e341de415d6b99296/rsi/TEACHING-ROADMAP.md

Illustration: https://github.com/dlmastery/simple-coding-harness/blob/7db77bd8d38aa5f23dc4180e341de415d6b99296/rsi/assets/illustrations/course-mindmap-v2.png
The figure explains a mechanism. Its illustrative cards do not establish an empirical result.

# 03 · The complete data-science task

Teaching point: Define the prediction. Inspect the data. Build a baseline. Diagnose errors. Compare a change. Report what generalizes.

RSI still depends on sound data science. A sophisticated
controller cannot rescue an invalid target or a leaking split. Follow one
row through this picture and ask when its target may influence a decision.
The core course uses bike-demand regression. The repaired research extension
also uses classification and controlled regression tasks.

Source: theme 00 and benchmark-repair protocol.

Course evidence and reading:
https://github.com/dlmastery/simple-coding-harness/blob/7db77bd8d38aa5f23dc4180e341de415d6b99296/rsi/00_start_here/README.md
https://github.com/dlmastery/simple-coding-harness/blob/7db77bd8d38aa5f23dc4180e341de415d6b99296/how-did-i-generate-it/rsi/validation/BENCHMARK-REPAIR-PROTOCOL.md

Illustration: https://github.com/dlmastery/simple-coding-harness/blob/7db77bd8d38aa5f23dc4180e341de415d6b99296/rsi/assets/illustrations/data-science-process-v4.png
The figure explains a mechanism. Its illustrative cards do not establish an empirical result.

# 04 · Data available at prediction time

Teaching point: An input must exist when the prediction is made.

The bike component counts sum to total demand. Giving both
components to the predictor reveals the answer. Ask students to identify the
shortcut before explaining it. Observed weather also changes the question:
retrospective demand estimation is different from forecasting tomorrow with
unknown weather. State the intended use before interpreting accuracy.

Source: lab 00.01 and the bike data card.

Course evidence and reading:
https://github.com/dlmastery/simple-coding-harness/blob/7db77bd8d38aa5f23dc4180e341de415d6b99296/rsi/00_start_here/step_01_meet_the_task/README.md

Illustration: https://github.com/dlmastery/simple-coding-harness/blob/7db77bd8d38aa5f23dc4180e341de415d6b99296/rsi/assets/illustrations/target-leakage-v2.png
The figure explains a mechanism. Its illustrative cards do not establish an empirical result.

# 05 · Training, selection and final evaluation

Teaching point: Training fits parameters. Selection chooses among candidates. Final evaluation tests the frozen choice.

A final score stops being a clean test if we use it to choose
the next revision. This applies to whole procedures as well as individual
models. New rows test row generalization. New task instances test a broader
question, but new seeds from a known generator still do not establish transfer
to a new scientific domain. Our local filesystem boundary is procedural.

Source: theme 08 and discovery-evaluation protocol.

Course evidence and reading:
https://github.com/dlmastery/simple-coding-harness/blob/7db77bd8d38aa5f23dc4180e341de415d6b99296/rsi/08_measuring_improvement/README.md
https://github.com/dlmastery/simple-coding-harness/blob/7db77bd8d38aa5f23dc4180e341de415d6b99296/rsi/evidence/2026-09-22/discovery-final/README.md

Illustration: https://github.com/dlmastery/simple-coding-harness/blob/7db77bd8d38aa5f23dc4180e341de415d6b99296/rsi/assets/illustrations/freeze-before-final-v2.png
The figure explains a mechanism. Its illustrative cards do not establish an empirical result.

# 06 · A baseline with one learned number

Teaching point: A training-median predictor gives a simple reference for regression.

Work through the small illustrated example before discussing
larger models. The predictor learns its constant from training rows. We then
measure error on different rows. A weak baseline helps teach the metric, but
an effectiveness study also needs strong baseline procedures. Beating the
training median does not by itself show that a research agent improved.

Source: lab 00.03 and the figure's illustrative-number caption.

Course evidence and reading:
https://github.com/dlmastery/simple-coding-harness/blob/7db77bd8d38aa5f23dc4180e341de415d6b99296/rsi/00_start_here/step_03_one_attempt/README.md

Illustration: https://github.com/dlmastery/simple-coding-harness/blob/7db77bd8d38aa5f23dc4180e341de415d6b99296/rsi/assets/illustrations/training-median-baseline-v1.png
The figure explains a mechanism. Its illustrative cards do not establish an empirical result.

# 07 · One model change

Teaching point: A hypothesis connects an observed error to a proposed experiment.

Ask students to name one change and what observation would
count against it. A record that says only “try a better model” gives little
insight into the decision. Keep the old prediction file. A failed candidate
is useful evidence when its assumptions and cost remain visible. At this
stage, the research procedure stays fixed.

Source: early experiment labs and run-ml-experiment skill.

Course evidence and reading:
https://github.com/dlmastery/simple-coding-harness/blob/7db77bd8d38aa5f23dc4180e341de415d6b99296/rsi/02_loop_engineering/step_01_why_repeat/README.md
https://github.com/dlmastery/simple-coding-harness/blob/7db77bd8d38aa5f23dc4180e341de415d6b99296/rsi/skills/run-ml-experiment/SKILL.md

Illustration: https://github.com/dlmastery/simple-coding-harness/blob/7db77bd8d38aa5f23dc4180e341de415d6b99296/rsi/assets/illustrations/one-factor-model-change-v1.png
The figure explains a mechanism. Its illustrative cards do not establish an empirical result.

# 08 · Skills, agents and tools

Teaching point: A skill supplies a procedure. An agent applies it. A tool executes an operation. A checker examines the result.

Students give instructions in ordinary language. The coding
agent writes code and configuration. A Markdown file alone does not prove
that an agent followed it. Ask students to point to a decision in an execution
trace and the instruction that governed it. This distinction becomes central
when we claim that a revised skill helped later work.

Source: theme 01 and the shared course skills.

Course evidence and reading:
https://github.com/dlmastery/simple-coding-harness/blob/7db77bd8d38aa5f23dc4180e341de415d6b99296/rsi/01_process_without_loops/README.md
https://github.com/dlmastery/simple-coding-harness/blob/7db77bd8d38aa5f23dc4180e341de415d6b99296/rsi/skills/README.md

Illustration: https://github.com/dlmastery/simple-coding-harness/blob/7db77bd8d38aa5f23dc4180e341de415d6b99296/rsi/assets/illustrations/skill-agent-tool-check-v2.png
The figure explains a mechanism. Its illustrative cards do not establish an empirical result.

# 09 · A bounded improvement loop

Teaching point: Each attempt reads state, makes one decision and records an outcome.

A loop needs more than a repeat command. It needs a stopping
condition, a retained best result and a record of consumed resources. Ask what
happens if the process crashes just after a fit starts. Restarting the program
must not erase that attempt. Repetition under a fixed rule is useful automation;
we have not yet changed the improvement rule.

Source: theme 02.

Course evidence and reading:
https://github.com/dlmastery/simple-coding-harness/blob/7db77bd8d38aa5f23dc4180e341de415d6b99296/rsi/02_loop_engineering/README.md

Illustration: https://github.com/dlmastery/simple-coding-harness/blob/7db77bd8d38aa5f23dc4180e341de415d6b99296/rsi/assets/illustrations/bounded-loop-v1.png
The figure explains a mechanism. Its illustrative cards do not establish an empirical result.

# 10 · A graph of dependent work

Teaching point: A result depends on the correct data, code and earlier decisions.

A graph makes dependencies explicit. If an input changes,
some descendants need new evidence. A table that combines scores from different
datasets can look convincing while answering no valid comparison. Follow one
dependency and ask which hash or record establishes that it is the intended
input. Graph completeness also matters: an omitted edge can hide a requirement.

Source: theme 03 and graph-reconciliation evidence.

Course evidence and reading:
https://github.com/dlmastery/simple-coding-harness/blob/7db77bd8d38aa5f23dc4180e341de415d6b99296/rsi/03_graph_engineering/README.md
https://github.com/dlmastery/simple-coding-harness/blob/7db77bd8d38aa5f23dc4180e341de415d6b99296/rsi/evidence/2026-09-22/graph-reconciliation/README.md

Illustration: https://github.com/dlmastery/simple-coding-harness/blob/7db77bd8d38aa5f23dc4180e341de415d6b99296/rsi/assets/illustrations/artifact-dependencies-v2.png
The figure explains a mechanism. Its illustrative cards do not establish an empirical result.

# 11 · Meaning and validity rules

Teaching point: An ontology names the objects and the relationships that must hold.

A workflow graph describes what depends on what. Domain rules
describe what those objects mean. A valid numerical score can still refer to
the wrong target, time period or unit. Ask students for a rule that software
can check directly and a rule that needs domain judgment. Do not equate adding
an ontology file with establishing the truth of every statement in it.

Source: theme 04.

Course evidence and reading:
https://github.com/dlmastery/simple-coding-harness/blob/7db77bd8d38aa5f23dc4180e341de415d6b99296/rsi/04_ontology_engineering/README.md

Illustration: https://github.com/dlmastery/simple-coding-harness/blob/7db77bd8d38aa5f23dc4180e341de415d6b99296/rsi/assets/illustrations/graph-ontology-v1.png
The figure explains a mechanism. Its illustrative cards do not establish an empirical result.

# 12 · The complete research system

Teaching point: Reliable behavior depends on how the components work together.

Improvements can come from coordination even when component
models stay fixed. A planner may request a candidate that a tool cannot build.
A checker may validate the wrong output. Trace one request across the system
and show the joins that keep its identity intact. Later, when components
change, we must retest their combined behavior.

Source: theme 05.

Course evidence and reading:
https://github.com/dlmastery/simple-coding-harness/blob/7db77bd8d38aa5f23dc4180e341de415d6b99296/rsi/05_system_intelligence/README.md

Illustration: https://github.com/dlmastery/simple-coding-harness/blob/7db77bd8d38aa5f23dc4180e341de415d6b99296/rsi/assets/illustrations/system-coordination-v3.png
The figure explains a mechanism. Its illustrative cards do not establish an empirical result.

# 13 · A harness generated from a brief

Teaching point: A readable task brief guides the creation of an executable harness.

The builder creates a harness for the requested task. The
generated code still needs execution checks. Distinguish a usable generated
artifact from a better builder. A builder that produces a second harness
under unchanged instructions has demonstrated reuse. Evidence that the builder
itself improved requires a comparison of builder versions under matched work.

Source: theme 06 and capstone-harness evidence.

Course evidence and reading:
https://github.com/dlmastery/simple-coding-harness/blob/7db77bd8d38aa5f23dc4180e341de415d6b99296/rsi/06_meta_harness_engineering/README.md
https://github.com/dlmastery/simple-coding-harness/blob/7db77bd8d38aa5f23dc4180e341de415d6b99296/rsi/evidence/2026-09-21/capstone-harness/README.md

Illustration: https://github.com/dlmastery/simple-coding-harness/blob/7db77bd8d38aa5f23dc4180e341de415d6b99296/rsi/assets/illustrations/meta-harness-v2.png
The figure explains a mechanism. Its illustrative cards do not establish an empirical result.

# 14 · The meanings of self-*

Teaching point: The changed object determines the claim.

Introduce reflection, organization, emergence, adaptation and
self-improvement as distinct questions. Researchers use these terms in
different ways, so keep the source's definition nearby. A changed assignment
of work does not establish changed model parameters. An unexpected pattern
does not establish that the system rewrote its improver. Ask students to name
an artifact that could support each label.

Source: theme 07 and glossary.

Course evidence and reading:
https://github.com/dlmastery/simple-coding-harness/blob/7db77bd8d38aa5f23dc4180e341de415d6b99296/rsi/07_understanding_self_star/README.md
https://github.com/dlmastery/simple-coding-harness/blob/7db77bd8d38aa5f23dc4180e341de415d6b99296/rsi/GLOSSARY.md

Illustration: https://github.com/dlmastery/simple-coding-harness/blob/7db77bd8d38aa5f23dc4180e341de415d6b99296/rsi/assets/illustrations/self-star-v2.png
The figure explains a mechanism. Its illustrative cards do not establish an empirical result.

# 15 · Reflection as a testable hypothesis

Teaching point: A critique matters when it changes a checked decision.

A fluent critique can be wrong. Convert it into a proposed
change and a falsifying observation. Preserve the prediction made before the
experiment, then compare it with the outcome. The useful evidence is the
resulting behavior and its measurement, rather than how persuasive the critique
sounds. This keeps reflection connected to an external check.

Source: self-reflection lesson and scientific-claim evidence.

Course evidence and reading:
https://github.com/dlmastery/simple-coding-harness/blob/7db77bd8d38aa5f23dc4180e341de415d6b99296/rsi/07_understanding_self_star/step_02_reflection/README.md

Illustration: https://github.com/dlmastery/simple-coding-harness/blob/7db77bd8d38aa5f23dc4180e341de415d6b99296/rsi/assets/illustrations/reflection-hypothesis-checks-v2.png
The figure explains a mechanism. Its illustrative cards do not establish an empirical result.

# 16 · Organization and emergent patterns

Teaching point: Shared rules can change coordination while the rules themselves stay fixed.

A shared queue can change which worker takes a task. That is
an organizational mechanism. Discuss how a new coordination pattern might
appear without a learned update. Ask whether the pattern improves useful
throughput after coordination overhead. A surprising behavior, a useful
behavior and a revised improvement process require different evidence.

Source: labs 07.05–07.06 and their scheduling evidence.

Course evidence and reading:
https://github.com/dlmastery/simple-coding-harness/blob/7db77bd8d38aa5f23dc4180e341de415d6b99296/rsi/07_understanding_self_star/step_05_organization/README.md
https://github.com/dlmastery/simple-coding-harness/blob/7db77bd8d38aa5f23dc4180e341de415d6b99296/rsi/07_understanding_self_star/step_06_emergence/README.md

Illustration: https://github.com/dlmastery/simple-coding-harness/blob/7db77bd8d38aa5f23dc4180e341de415d6b99296/rsi/assets/illustrations/organization-shared-queue-v1.png
The figure explains a mechanism. Its illustrative cards do not establish an empirical result.

# 17 · Solver, improver and evaluator

Teaching point: The solver does the task. The improver changes its procedure. The evaluator judges the resulting work.

Use one concrete ML search as the example. A model parameter
belongs to the solution. An experiment-allocation policy belongs to the
research procedure. A rule that chooses among revisions to that policy belongs
to the improver. The external comparison stays fixed while internal procedures
change. Otherwise a system can appear to improve by changing what counts as success.

Source: lab 09.01 and improve-research-skill skill.

Course evidence and reading:
https://github.com/dlmastery/simple-coding-harness/blob/7db77bd8d38aa5f23dc4180e341de415d6b99296/rsi/09_recursive_self_improvement/step_01_three_objects/README.md
https://github.com/dlmastery/simple-coding-harness/blob/7db77bd8d38aa5f23dc4180e341de415d6b99296/rsi/skills/improve-research-skill/SKILL.md

Illustration: https://github.com/dlmastery/simple-coding-harness/blob/7db77bd8d38aa5f23dc4180e341de415d6b99296/rsi/assets/illustrations/name-experiment-objects-v2.png
The figure explains a mechanism. Its illustrative cards do not establish an empirical result.

# 18 · Evidence of recursive use

Teaching point: A later improvement round must use the revised improver.

Saving a revised file establishes that a proposal exists.
Loading it later establishes source use. A trace showing its rule governing
a different decision adds behavioral evidence. A fair comparison then asks
whether the resulting process improves new work. Keep these observations
separate. A short lineage can demonstrate the mechanism without establishing
sustained acceleration or broad autonomy.

Source: labs 09.03–09.06 and MetaSkill method audit.

Course evidence and reading:
https://github.com/dlmastery/simple-coding-harness/blob/7db77bd8d38aa5f23dc4180e341de415d6b99296/rsi/09_recursive_self_improvement/step_04_inherit/README.md

Illustration: https://github.com/dlmastery/simple-coding-harness/blob/7db77bd8d38aa5f23dc4180e341de415d6b99296/rsi/assets/illustrations/inherited-improver-v1.png
The figure explains a mechanism. Its illustrative cards do not establish an empirical result.

# 19 · Why the original results were mostly zero

Teaching point: Similar recipe sets often produced the same best candidate. Some reported efficiency wins still executed every fit.

Explain the original failure directly. Reordering the same
small recipe set often leaves the winning model unchanged. Labeling later
fits as wasted does not mean the program avoided them. Small validation sets
also made policy changes fragile. These issues motivated a search-space pilot,
actual inherited workspaces, real stopping decisions and separate task-level
evaluation. Preserve the negative historical results.

Source: RSI-RESULTS-DIAGNOSIS-2026-09-22.md.

Course evidence and reading:
https://github.com/dlmastery/simple-coding-harness/blob/7db77bd8d38aa5f23dc4180e341de415d6b99296/how-did-i-generate-it/rsi/validation/RSI-RESULTS-DIAGNOSIS-2026-09-22.md
https://github.com/dlmastery/simple-coding-harness/blob/7db77bd8d38aa5f23dc4180e341de415d6b99296/rsi/RESULTS-GUIDE.md

# 20 · A fair procedure comparison

Teaching point: Same tasks. Same allowed resources. Frozen procedures. Separate final rows.

Equal allowances do not require equal spending. A policy may
stop early, but the report must show the quality it gives up or preserves.
Include failures and development overhead. The current experiment reports
model-fit time separately from worker-process time because process startup
can dominate small laptop jobs. Unknown agent inference cost prevents a claim
about net total research cost.

Source: discovery-evaluation protocol and research-cost ledger.

Course evidence and reading:
https://github.com/dlmastery/simple-coding-harness/blob/7db77bd8d38aa5f23dc4180e341de415d6b99296/rsi/evidence/2026-09-22/discovery-final/README.md
https://github.com/dlmastery/simple-coding-harness/blob/7db77bd8d38aa5f23dc4180e341de415d6b99296/rsi/08_measuring_improvement/step_03_cost/README.md

Illustration: https://github.com/dlmastery/simple-coding-harness/blob/7db77bd8d38aa5f23dc4180e341de415d6b99296/rsi/assets/illustrations/matched-search-budgets-v1.png
The figure explains a mechanism. Its illustrative cards do not establish an empirical result.

# 21 · Research benchmark scale

Teaching point: Laptop lessons expose mechanisms. Research benchmarks demand broader search, stronger baselines and separate evaluation.

Give concrete scale without treating the benchmarks as a single
league table. RSI-Exam describes up to twelve hours per task with separate
hidden grading. MLE-bench recommends substantially larger resources than a
laptop, although some individual tasks are small. Explain which comparison
question each benchmark asks. A faster small pipeline search does not establish
that an agent can engineer a correct GPU kernel or solve a new research domain.

Source: ../research/2026-09-22-BENCHMARK-SCALE.md and its primary links. Identify
MLE-bench as an older foundation, separate from recent releases.

Course evidence and reading:
https://github.com/dlmastery/simple-coding-harness/blob/7db77bd8d38aa5f23dc4180e341de415d6b99296/how-did-i-generate-it/rsi/research/2026-09-22-BENCHMARK-SCALE.md

Primary benchmark documentation, inspected 22 September 2026:
https://github.com/aiming-lab/RSI-Exam/blob/main/README.md
https://github.com/openai/mle-bench/blob/main/README.md
The table reports dated maintainer specifications, not our benchmark execution.

# 22 · The research studio

Teaching point: Each method changes a specific part of scientific work.

Use the map to locate the methods rather than asking students
to memorize all names. The important questions are what changes, what feedback
drives the change, and what later evidence supports it. The studio includes
source reading as well as experiments. A paper's reported result, a classroom
adaptation and an independent reproduction must remain distinct.

Source: theme 10 overview and research sweep.

Course evidence and reading:
https://github.com/dlmastery/simple-coding-harness/blob/7db77bd8d38aa5f23dc4180e341de415d6b99296/rsi/10_research_studio/README.md
https://github.com/dlmastery/simple-coding-harness/blob/7db77bd8d38aa5f23dc4180e341de415d6b99296/rsi/research/README.md

Illustration: https://github.com/dlmastery/simple-coding-harness/blob/7db77bd8d38aa5f23dc4180e341de415d6b99296/rsi/assets/illustrations/research-studio-map-v3.png
The figure explains a mechanism. Its illustrative cards do not establish an empirical result.

# 23 · Dream-RSI: discovery history and replay

Teaching point: A recorded tree supports policy experiments without repeating every fit.

A policy can ask to start again from the root or continue an
observed leaf. Replay exposes the recorded continuation. It cannot supply a
score for an untried branch. In the laptop adaptation, the inner proposer is
a fixed program and the coding agent revises the exploration policy. Explain
this simplification before showing local results.

Source: Dream-RSI v1, https://arxiv.org/html/2609.14858v1, and online-discovery evidence.

Course evidence and reading:
https://github.com/dlmastery/simple-coding-harness/blob/7db77bd8d38aa5f23dc4180e341de415d6b99296/rsi/10_research_studio/02_dream_rsi/step_08_replay/README.md
https://github.com/dlmastery/simple-coding-harness/blob/7db77bd8d38aa5f23dc4180e341de415d6b99296/rsi/evidence/2026-09-22/online-discovery/README.md

Illustration: https://github.com/dlmastery/simple-coding-harness/blob/7db77bd8d38aa5f23dc4180e341de415d6b99296/rsi/assets/illustrations/replay-boundary-v2.png
The figure explains a mechanism. Its illustrative cards do not establish an empirical result.

# 24 · Deployment after replay

Teaching point: A selected policy needs a new online test.

The recorded worlds determine which counterfactual questions
replay can answer. Our development cycle promoted one revision, then retained
it in the next round. Later runs loaded its exact source and added new trees
to the history. That establishes the cycle's operation. The paired evaluation
is the separate test of whether the revised policy helps new task instances.

Source: online-discovery archive and POLICY-LINEAGE-CHECKS.csv.

Course evidence and reading:
https://github.com/dlmastery/simple-coding-harness/blob/7db77bd8d38aa5f23dc4180e341de415d6b99296/rsi/evidence/2026-09-22/online-discovery/README.md

Illustration: https://github.com/dlmastery/simple-coding-harness/blob/7db77bd8d38aa5f23dc4180e341de415d6b99296/rsi/assets/illustrations/replay-to-online-v2.png
The figure explains a mechanism. Its illustrative cards do not establish an empirical result.

# 25 · RSIAgent: exploration and actor memory

Teaching point: Checked outcomes inform memory that the actor uses during later work.

The outcome verifier checks what happened. The actor decides
what lesson to retain. A correct score does not make every generalization from
it correct. Explain broad practice followed by focused investigation, then a
comparison with learning disabled. The paper includes target-conditioned
practice, so distinguish that setting from evaluation on new tasks. State the
actual context separation used in each local experiment.

Source: RSIAgent v1, https://arxiv.org/html/2609.15364v1, and repaired-method requirements.

Course evidence and reading:
https://github.com/dlmastery/simple-coding-harness/blob/7db77bd8d38aa5f23dc4180e341de415d6b99296/rsi/10_research_studio/01_memory_and_exploration/step_04_actor_memory/README.md

Illustration: https://github.com/dlmastery/simple-coding-harness/blob/7db77bd8d38aa5f23dc4180e341de415d6b99296/rsi/assets/illustrations/actor-memory-v2.png
The figure explains a mechanism. Its illustrative cards do not establish an empirical result.

# 26 · Recuris: working state and reusable experience

Teaching point: Current state supports this run. Retained experience can guide later runs.

A pending action and a reusable research lesson serve different
purposes. Mixing them can preserve obsolete state as if it were a general
rule. Ask students which record they would carry into a new task. A memory
change needs evidence, scope and later-use checks. Its value depends on the
retrieval and execution process, not simply on keeping more text.

Source: Recuris, https://arxiv.org/abs/2608.24876, and the course's method notes.

Course evidence and reading:
https://github.com/dlmastery/simple-coding-harness/blob/7db77bd8d38aa5f23dc4180e341de415d6b99296/rsi/10_research_studio/01_memory_and_exploration/step_06_working_and_experience/README.md

Illustration: https://github.com/dlmastery/simple-coding-harness/blob/7db77bd8d38aa5f23dc4180e341de415d6b99296/rsi/assets/illustrations/working-state-and-experience-v1.png
The figure explains a mechanism. Its illustrative cards do not establish an empirical result.

# 27 · AIDE2: improving the researcher

Teaching point: An outer process changes the harness that runs inner ML searches.

Draw attention to the unit of evaluation: an entire inner
search. Its proposal operators, context and parent selection affect what the
search can discover. Count the losing inner searches as part of the outer
cost. A changed harness must execute later searches under a fair comparison.
A rearranged list that still evaluates every recipe may leave quality unchanged.

The completed classroom study rewrites full researchers. Each researcher
executes twelve model attempts and uses observed feedback to choose later
experiments. The outer rule compares whole researchers on six development
tasks. I1's child narrowly passes that gate. The same frozen improver then
generates another researcher from its retained parent, and that researcher
actually runs on six reserved tasks. The final comparison remains inconclusive.
The coding agent wrote the bounded improvers. Separate LLM agents, autonomous
researcher invention and the paper's full system were not tested.

Local evidence: complete researcher and later use: https://github.com/dlmastery/simple-coding-harness/blob/7db77bd8d38aa5f23dc4180e341de415d6b99296/rsi/evidence/2026-09-22/nested-research-evaluation/README.md.

Source: Weco report, https://www.weco.ai/blog/first-evidence-of-recursive-self-improvement,
and 2026-09-21-AIDE-METHOD-AUDIT.md. The report is an explicitly dated older foundation.

Course evidence and reading:
https://github.com/dlmastery/simple-coding-harness/blob/7db77bd8d38aa5f23dc4180e341de415d6b99296/rsi/10_research_studio/04_aide2/step_14_outer_research/README.md
https://github.com/dlmastery/simple-coding-harness/blob/7db77bd8d38aa5f23dc4180e341de415d6b99296/rsi/evidence/2026-09-22/nested-research-evaluation/README.md

Illustration: https://github.com/dlmastery/simple-coding-harness/blob/7db77bd8d38aa5f23dc4180e341de415d6b99296/rsi/assets/illustrations/nested-research-v2.png
The figure explains a mechanism. Its illustrative cards do not establish an empirical result.

# 28 · Ignition is a separate test

Teaching point: A better inner researcher may still fail in the outer improvement role.

Moving a discovered researcher into the role that improves
researchers changes the task. Success at model search does not guarantee
success at harness design. The source audit records that the reported ignition
efficiency difference was not statistically significant. Keep that outcome
distinct from the inner-researcher improvement and from evidence of sustained
recursive gains.

Source: Weco report and AIDE method audit above.

Course evidence and reading:
https://github.com/dlmastery/simple-coding-harness/blob/7db77bd8d38aa5f23dc4180e341de415d6b99296/rsi/10_research_studio/04_aide2/step_15_ignition/README.md

Illustration: https://github.com/dlmastery/simple-coding-harness/blob/7db77bd8d38aa5f23dc4180e341de415d6b99296/rsi/assets/illustrations/ignition-role-transfer-v1.png
The figure explains a mechanism. Its illustrative cards do not establish an empirical result.

# 29 · MetaSkill: task skills and their updater

Teaching point: Fast updates change task skills. Slower updates change how those skills evolve.

The source coordinates several meta-skill roles, including
analysis, retrieval, allocation, proposal and evolution. A later round must
use the revised updater, not merely store it beside the old one. State which
roles and branch mechanisms the local adaptation implements. The classroom
fixture and the paper's full system support different claims.

The later public-task study reads five versioned role files inside one
author context. Those files do not create five independent agents. The
complete-researcher extension separately checks that a changed improver
creates a later researcher and that this researcher runs. Its primary
comparison has two gains, three ties and one regression. Show the later
execution trace before discussing whether those results establish a benefit.

Local evidence: role-file comparison: https://github.com/dlmastery/simple-coding-harness/blob/7db77bd8d38aa5f23dc4180e341de415d6b99296/rsi/evidence/2026-09-22/tabular-comparison/README.md
and generated-researcher comparison: https://github.com/dlmastery/simple-coding-harness/blob/7db77bd8d38aa5f23dc4180e341de415d6b99296/rsi/evidence/2026-09-22/nested-research-evaluation/README.md.

Source: MetaSkill-Evolve v1, https://arxiv.org/html/2607.05297v1, and its method audit.
This is an explicitly dated older foundation.

Course evidence and reading:
https://github.com/dlmastery/simple-coding-harness/blob/7db77bd8d38aa5f23dc4180e341de415d6b99296/rsi/10_research_studio/05_meta_skill_evolution/step_17_meta_skills/README.md

Illustration: https://github.com/dlmastery/simple-coding-harness/blob/7db77bd8d38aa5f23dc4180e341de415d6b99296/rsi/assets/illustrations/meta-skill-schedules-v3.png
The figure explains a mechanism. Its illustrative cards do not establish an empirical result.

# 30 · ScientistTwo: a chain of scientific evidence

Teaching point: A scientific claim needs experiments, ablations and a response to criticism.

A plausible hypothesis is the start of a scientific process.
Ask which observation would distinguish its mechanism from a simpler
explanation. A review score supplies feedback, but its meaning depends on who
or what produced it. Distinguish automated review from publication acceptance
and independent replication. Connect each revised claim to the experiment
that changed the evidence.

Source: ScientistTwo, https://arxiv.org/abs/2609.19644, and scientist-method audit.

Course evidence and reading:
https://github.com/dlmastery/simple-coding-harness/blob/7db77bd8d38aa5f23dc4180e341de415d6b99296/rsi/10_research_studio/06_scientist_two/README.md
https://github.com/dlmastery/simple-coding-harness/blob/7db77bd8d38aa5f23dc4180e341de415d6b99296/rsi/evidence/2026-09-21/scientist-labs/README.md

Illustration: https://github.com/dlmastery/simple-coding-harness/blob/7db77bd8d38aa5f23dc4180e341de415d6b99296/rsi/assets/illustrations/scientific-claim-v2.png
The figure explains a mechanism. Its illustrative cards do not establish an empirical result.

# 31 · ScienceBuddy: model and harness co-evolution

Teaching point: Human scientific feedback can inform both the harness and model training.

Changing instructions or tools and changing model weights are
different interventions. Their effects may interact. Explain the source's
human-grounded tasks and evaluation rubrics before describing coupled updates.
The laptop activities do not train a frontier model. Any paper-reported
accuracy figure must carry its exact benchmark, comparison and source in the
notes, separate from our measured classroom results.

Source: ScienceBuddy, https://arxiv.org/abs/2609.17523, and sciencebuddy-result-audit evidence.

Course evidence and reading:
https://github.com/dlmastery/simple-coding-harness/blob/7db77bd8d38aa5f23dc4180e341de415d6b99296/rsi/10_research_studio/07_sciencebuddy/README.md

Illustration: https://github.com/dlmastery/simple-coding-harness/blob/7db77bd8d38aa5f23dc4180e341de415d6b99296/rsi/assets/illustrations/model-harness-v4.png
The figure explains a mechanism. Its illustrative cards do not establish an empirical result.

# 32 · Fewer executed fits on sixteen tasks

Teaching point: The evolved policy used 55 search fits versus broad search's 192. Final quality improved on three tasks, tied on twelve and worsened on one. The overall quality difference remains uncertain.

These bars count actual executed searches. The policy saved
137 fits against broad search. A simpler stopping ablation saved 108, so much
of the saving comes from stopping. The evolved allocation saved another 29.
Ask students why the stopping ablation belongs on the slide. Its presence
helps separate the contribution of stopping from the branch-allocation change.

The primary normalized loss difference is -0.002820. Its exploratory 95%
task-bootstrap interval is [-0.006548, +0.000010], which includes zero.
Task 8123 improves from 0.901803 to 0.913071 balanced accuracy. Task 8106's
MAE worsens from 0.245790 to 0.246037. Discuss both. A favorable mean alone
does not establish a reliable predictive advantage.

The paired phase incurred 715 searches and 80 scoring refits. A disclosed
standby interruption adds two admitted attempts in the excluded case, for
797 attempts. All eighty retained candidates were frozen before scoring.
Development, the earlier shakedown and agent inference add costs outside
these bars. The experiment therefore supports lower search work in this
setting, while total research-cost savings remain unknown.

These are new instances of known synthetic families. The developer knew the
generator and wrote the policy changes. The experiment does not establish
unseen-domain transfer, full Dream-RSI reproduction or an improved updater.
Transition: the next comparison tests complete researchers generated by two
different improvers on public classification and regression tasks.

Sources: full report: https://github.com/dlmastery/simple-coding-harness/blob/7db77bd8d38aa5f23dc4180e341de415d6b99296/rsi/evidence/2026-09-22/discovery-final/README.md,
individual results: https://github.com/dlmastery/simple-coding-harness/blob/7db77bd8d38aa5f23dc4180e341de415d6b99296/rsi/evidence/2026-09-22/discovery-final/RESULTS.csv,
paired intervals: https://github.com/dlmastery/simple-coding-harness/blob/7db77bd8d38aa5f23dc4180e341de415d6b99296/rsi/evidence/2026-09-22/discovery-final/PAIRED.csv
and incurred costs: https://github.com/dlmastery/simple-coding-harness/blob/7db77bd8d38aa5f23dc4180e341de415d6b99296/rsi/evidence/2026-09-22/discovery-final/INCURRED-COSTS.csv.

Course evidence and reading:
https://github.com/dlmastery/simple-coding-harness/blob/7db77bd8d38aa5f23dc4180e341de415d6b99296/rsi/evidence/2026-09-22/discovery-final/README.md
https://github.com/dlmastery/simple-coding-harness/blob/7db77bd8d38aa5f23dc4180e341de415d6b99296/rsi/evidence/2026-09-22/discovery-final/RESULTS.csv
https://github.com/dlmastery/simple-coding-harness/blob/7db77bd8d38aa5f23dc4180e341de415d6b99296/rsi/evidence/2026-09-22/discovery-final/PAIRED.csv

# 33 · Later researchers have mixed results

Teaching point: I1's later researcher improved two tasks, tied three and worsened one against I0 and the parent. The overall effect remains inconclusive.

The outer development gate accepted I1's first researcher
after two small gains and four ties. It rejected I0's child. Both frozen
improvers then generated a second researcher from their retained parent and
completed traces. The second researchers actually executed the reserved-task
searches. This is the evidence of later use.

On spam, I1's balanced accuracy is 0.948947 versus the parent's 0.944437.
On satellite pixels it is 0.846324 versus 0.844385. On housing, I1's MAE rises
to 50,276.97 from 49,038.58. A larger MAE is worse. DNA, protein and grid
have tied aggregate scores in this comparison. Ask students why highlighting
only spam would give a misleading account of the study.

The subsequent prediction audit explains those ties. Protein and grid select
the same constructor as the parent. DNA selects different SVM settings but
makes the same class prediction on every final row. I1 nevertheless changes
all four experiments after the shared eight-model start on every task.
Different search behavior therefore need not change the final predictions.
The frozen-outcome diagnosis: https://github.com/dlmastery/simple-coding-harness/blob/7db77bd8d38aa5f23dc4180e341de415d6b99296/how-did-i-generate-it/rsi/validation/nested-outcome-diagnosis/README.md
also records selection/final rank reversals without retraining.

All four intervals include zero. The experiment uses six public tasks, one
model seed and 10,000 task-bootstrap draws stratified by classification or
regression. These are exploratory intervals without multiplicity adjustment.
They neither prove equality nor establish an overall advantage. The sign of
the mean also depends on the control. Keep the prespecified I1–I0 comparison
visible when discussing the favorable mean against fixed search.

Every arm used twelve search attempts per task. The full study incurred 624
attempts: 216 development searches, 18 development refits, 360 reserved
searches and 30 reserved refits. Losing searches count. There is no saved-fit
claim in this study. The final audit independently checks predictions,
selection freezes, source inheritance and feedback-dependent choices.

The improvers are bounded programs written by the coding agent. The study
does not train model weights or demonstrate autonomous invention. Public
files provide a procedural evaluation boundary. These final tasks are now
exposed and cannot serve as untouched tests for a revision motivated by them.
Transition: separate the verified mechanism from the scientific claim it
can support, then use that distinction in the capstones.

Sources: complete report: https://github.com/dlmastery/simple-coding-harness/blob/7db77bd8d38aa5f23dc4180e341de415d6b99296/rsi/evidence/2026-09-22/nested-research-evaluation/README.md,
unrounded contrasts: https://github.com/dlmastery/simple-coding-harness/blob/7db77bd8d38aa5f23dc4180e341de415d6b99296/rsi/evidence/2026-09-22/nested-research-evaluation/CONTRASTS.csv,
native scores: https://github.com/dlmastery/simple-coding-harness/blob/7db77bd8d38aa5f23dc4180e341de415d6b99296/rsi/evidence/2026-09-22/nested-research-evaluation/NATIVE-SCORES.csv
and development gate: https://github.com/dlmastery/simple-coding-harness/blob/7db77bd8d38aa5f23dc4180e341de415d6b99296/rsi/evidence/2026-09-22/nested-research-development/README.md.

Course evidence and reading:
https://github.com/dlmastery/simple-coding-harness/blob/7db77bd8d38aa5f23dc4180e341de415d6b99296/rsi/evidence/2026-09-22/nested-research-evaluation/README.md
https://github.com/dlmastery/simple-coding-harness/blob/7db77bd8d38aa5f23dc4180e341de415d6b99296/rsi/evidence/2026-09-22/nested-research-evaluation/CONTRASTS.csv

# 34 · What the evidence supports

Teaching point: Changed source, later execution, predictive benefit and total cost answer different questions. The repaired course demonstrates real changes and later use. Overall RSI quality gains remain unestablished.

A final score is one piece of evidence. A changed source hash
shows an edit. A trace can show that the changed instruction governed a later
decision. A matched comparison asks whether the changed process helped.
Ask students to make the strongest claim these records support, then name
the evidence required for a stronger claim.

Use this comparison matrix in discussion. It maps the user's original seven
concerns to shared experiments. Its seven rows are not seven independent
replications of the named systems.

| Original concern | Executed mechanism and later use | Predictive result | Resource result and limit |
|---|---|---|---|
| Proof | Frozen choices, separate final rows and recomputed predictions | Mixed quality outcomes | Costs preserved, agent inference unknown |
| Meta gate | Actual gate retention followed by generated-researcher execution | Small development gains, inconclusive reserved results | All 624 attempts count |
| Dream-RSI | Parent workspaces, replay-selected policy and later online searches | 3 gains, 12 ties, 1 regression versus broad | 55 versus 192 search fits, known synthetic families |
| Recuris | Current state separated from retained, checked experience | Memory beats random but loses to fixed overall | Full reproduction and general transfer unestablished |
| RSIAgent | Practice records, outcome checks and frozen-memory comparison | Same shared memory comparison | Author context, bounded task space |
| AIDE2 | Complete inner searches and executable outer rewrites | Later generated researchers have mixed results | Initial rejected study retained, no ignition claim |
| MetaSkill | Separate skill/updater versions and inherited later execution | I1 versus I0: 2 gains, 3 ties, 1 regression | Bounded programs, no independent multi-agent or weight-learning claim |

The construction repair also matters: a later assignment previously erased
some template changes. Distinct source text had constructed identical models.
The separately tested builder now preserves those changes. This fixes an
implementation defect, but it does not guarantee that the new candidate is
better. Use the housing regression to make that distinction concrete.

Sources: method requirements and evidence: https://github.com/dlmastery/simple-coding-harness/blob/7db77bd8d38aa5f23dc4180e341de415d6b99296/how-did-i-generate-it/rsi/validation/REPAIRED-METHOD-REQUIREMENTS.md,
memory comparison: https://github.com/dlmastery/simple-coding-harness/blob/7db77bd8d38aa5f23dc4180e341de415d6b99296/rsi/evidence/2026-09-22/tabular-comparison/README.md
and constructor repair: https://github.com/dlmastery/simple-coding-harness/blob/7db77bd8d38aa5f23dc4180e341de415d6b99296/rsi/evidence/2026-09-22/composition-repair/README.md.

Course evidence and reading:
https://github.com/dlmastery/simple-coding-harness/blob/7db77bd8d38aa5f23dc4180e341de415d6b99296/how-did-i-generate-it/rsi/validation/REPAIRED-METHOD-REQUIREMENTS.md
https://github.com/dlmastery/simple-coding-harness/blob/7db77bd8d38aa5f23dc4180e341de415d6b99296/rsi/RESULTS-GUIDE.md

Illustration: https://github.com/dlmastery/simple-coding-harness/blob/7db77bd8d38aa5f23dc4180e341de415d6b99296/rsi/assets/illustrations/evidence-beyond-score-v1.png
The figure explains a mechanism. Its illustrative cards do not establish an empirical result.

# 35 · The capstone projects

Teaching point: Build a harness. Test a retained lineage. Check portability. Audit a claim. Teach the evidence.

The capstones combine the course's earlier distinctions.
Students should bring a traceable portfolio rather than only their best score.
A clear negative result can satisfy a scientific learning objective when the
question, experiment and interpretation are sound. That does not automatically
satisfy a product objective that requires an effective improver. Name the
criterion the capstone actually tests.

Source: theme 11 and the five capstone briefs.

Course evidence and reading:
https://github.com/dlmastery/simple-coding-harness/blob/7db77bd8d38aa5f23dc4180e341de415d6b99296/rsi/11_capstones/README.md

Illustration: https://github.com/dlmastery/simple-coding-harness/blob/7db77bd8d38aa5f23dc4180e341de415d6b99296/rsi/assets/illustrations/capstone-map-v3.png
The figure explains a mechanism. Its illustrative cards do not establish an empirical result.

# 36 · Laptop and cluster execution

Teaching point: More compute changes the scale. The comparison contract still governs the experiment.

A larger cluster can support more expensive models or tasks.
Keep data roles, budgets, failure accounting and procedure freezes explicit.
Wall time and total compute can move in different directions under parallel
execution. A documented cluster adapter does not establish that we ran it.
State the tested backend and preserve untested capabilities as open work.

Source: scale-experiment skill and capstone-portability evidence.

Course evidence and reading:
https://github.com/dlmastery/simple-coding-harness/blob/7db77bd8d38aa5f23dc4180e341de415d6b99296/rsi/compute/README.md
https://github.com/dlmastery/simple-coding-harness/blob/7db77bd8d38aa5f23dc4180e341de415d6b99296/rsi/skills/scale-experiment/SKILL.md

Illustration: https://github.com/dlmastery/simple-coding-harness/blob/7db77bd8d38aa5f23dc4180e341de415d6b99296/rsi/assets/illustrations/compute-contract-v2.png
The figure explains a mechanism. Its illustrative cards do not establish an empirical result.

# 37 · Discussion and next experiment

Teaching point: What changed? What proves later use? What would you test next?

Give students a concrete example: a system saves a new policy,
uses fewer fits on later tasks and reports tied final quality. Ask what that
supports and what it leaves unresolved. Then ask what extra evidence would
support improvement of the improver. Let students propose the next experiment
before showing the course's quiz explanations and teaching roadmap.

Source: glossary, capstone 11.05 and TEACHING-ROADMAP.md.

Course evidence and reading:
https://github.com/dlmastery/simple-coding-harness/blob/7db77bd8d38aa5f23dc4180e341de415d6b99296/rsi/GLOSSARY.md
https://github.com/dlmastery/simple-coding-harness/blob/7db77bd8d38aa5f23dc4180e341de415d6b99296/rsi/11_capstones/step_05_teach_back/README.md
https://github.com/dlmastery/simple-coding-harness/blob/7db77bd8d38aa5f23dc4180e341de415d6b99296/rsi/TEACHING-ROADMAP.md

Illustration: https://github.com/dlmastery/simple-coding-harness/blob/7db77bd8d38aa5f23dc4180e341de415d6b99296/rsi/assets/illustrations/capstone-teach-back-v2.png
The figure explains a mechanism. Its illustrative cards do not establish an empirical result.
