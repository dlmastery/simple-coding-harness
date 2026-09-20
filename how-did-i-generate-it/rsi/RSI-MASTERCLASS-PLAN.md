# From Your First Agent Workflow to Recursive Self-Improvement

**Proposed masterclass rebuild — for review before implementation**

Prepared against repository commit `eed9cbbdf19c665ae54646253f303be85030798c` and the user's saved `rsiresearch.mhtml`. Research window: **20 August–19 September 2026**, with priority given to 6–19 September. Older foundations are dated separately. The broader [research inventory](RSI-RESEARCH-SWEEP.md) records sources, reading depth, gaps, and course decisions. This is a plan for review. Course production and runtime validation have not started.

The intended outcome is a student who can explain, construct, run, inspect, and evaluate a bounded recursively improving agent system through natural-language instructions and skills. The student can also identify which stronger claims their experiment has not established.

The course should feel like a patient teacher working beside the student: begin with something concrete, make a prediction, observe what actually happens, explain the result, and introduce the next idea only when its purpose is clear.

## 1. The commitments

1. **One understandable change at a time.** Students meet the problem before the mechanism that solves it.
2. **A practical path from the beginning.** Each lab produces something students can inspect, run, compare, or explain.
3. **Students communicate in ordinary language and readable Markdown.** The coding agent generates required code, schemas, configuration, and setup commands. Students need not handwrite Python, JSON, YAML, or a new configuration language.
4. **Skills are the learner's interface.** The distinction between a skill's instructions, the host coding agent, generated tools, and actual enforcement is taught explicitly.
5. **One coherent progression.** No competing build order and reading order.
6. **Themed directories.** Every theme has a welcoming README, a prerequisite bridge, a sequence of short labs, illustrations, and a checkpoint.
7. **Evidence determines the claim.** A changed file, more retries, a higher development score, or an impressive diagram cannot establish recursive improvement by itself.
8. **Research informs the teaching without overwhelming beginners.** Paper-specific terminology and reproduction details enter when the student has built the underlying mechanism.
9. **Visual explanations are part of the lesson.** Every visual has a teaching purpose, an accompanying explanation, and accessible alternative text.
10. **A complete course can contain an unsuccessful experiment.** Students must learn to report no improvement, regression, or insufficient evidence accurately.
11. **Every codelab ends with a quiz.** Questions test understanding and interpretation; answer explanations and targeted hints help the learner recover from mistakes.
12. **Every required lab has a student-laptop default.** Small regression and classification models train on the CPU. Foundation-model training is not required. A hosted coding agent can require internet access and paid usage. Each lab states these needs before the first action.
13. **Every lab builds an idea that lasts.** It ends with key takeaways, a quiz with explanations, and a short “What's next” section that explains why the next lesson is useful.
14. **The writing is clear and direct.** Use ASD-STE100 as the style reference. Use familiar words, short sentences, active verbs, consistent technical terms, and descriptive headings. Review for clarity as well as technical accuracy.
15. **The design can grow with the student's resources.** Keep task, evaluation, improvement, and compute interfaces separate. A student can later use larger datasets, harder models, GPUs, or a cluster through the same readable briefs and skills. The agent generates the required setup.

## 2. What the current course needs repaired

These are findings from inspection, not claims that every existing runtime has been reproduced.

| Observed issue | Evidence in the current repository | Planned repair |
|---|---|---|
| The entry point overwhelms beginners | `rsi/README.md` has 2,576 lines and reproduces extensive contracts, examples, and lesson content | Write a guided course introduction; move execution detail into short labs and technical references |
| The structure obscures progression | Eighteen flat `step_*` directories; README describes separate build and SDLC reading orders | Use numbered theme directories and one canonical sequence |
| Important foundations are missing | Ontology engineering and system intelligence have no dedicated teaching sequence | Add full themes before meta-harness construction |
| Machine representation dominates the explanation | 500 tracked RSI files include 144 JSON files; substantial duplicated skill trees | Make Markdown and natural-language prompts the student surface; maintain one canonical skill source with agent-specific projections |
| Terminology arrives too late | The final map groups self-organization and emergence together; early lessons already assign RSI levels | Add distinct experiments and counterexamples before the RSI theme |
| Persistence is presented too readily as RSI evidence | Lesson 06 is titled around a later run reading a file written by an earlier run | Separately demonstrate persistent learning, system improvement, inherited improvement procedures, and measured effectiveness |
| Claimed isolation exceeds the demonstrated boundary | Verifier instructions describe restricted inputs, but switching skills in one agent session does not establish independent context | Use an actual separate candidate/evaluator execution boundary where supported; label weaker demonstrations accurately |
| Hooks are too broad for the claims made | The sample hook accepts any matching frozen state or approval file anywhere under `runs/` | Bind checks to the exact run, candidate, action, and proposal; verify rejection behavior |
| Most offline checks establish document structure | Tests assert required strings, headings, mirrored files, and hook text; live tests use Claude behind an environment switch | Preserve useful linting and add behavior checks, negative cases, clean-start runs, and agent compatibility evidence |
| Some paper exercises are highly prescribed approximations | The AIDE² exercise prescribes a particular operator rewrite and meters fits rather than total research cost | Label adaptations, explain omissions, and introduce real proposal selection and full cost accounting where measurable |
| The new layout would silently evade current discovery | Both `run_tests.py` and `check_snippets.py` look for `rsi/step_*` | Update discovery and prove that all themed lessons remain discoverable |

The current work contains useful material to retain after review: small datasets, reusable task intents, bounded budgets, explicit stop conditions, version history, rollback, comparisons, and an initial paper map. The rebuild will retain sound mechanisms while rewriting their presentation and checking their claims.

The transcript is a source of questions and proposed ideas. Its claims will enter a correction ledger with a primary source and a resolution. In particular, sentences equating recursion with a reboot, equating learning with one autonomy level, or merging emergence with self-organization need careful correction.

## 3. The course architecture

Working blueprint: **99 small labs across 12 themes**, including **36 advanced labs in 12 themed subdirectories**. The wider research sweep adds eight distinct experiments. The count is provisional: beginner walkthroughs may split or combine labs. Learning dependencies and clarity determine the final count.

```text
rsi/
  README.md                         The welcoming, illustrated course walkthrough
  START-HERE.md                     The first successful agent session
  COURSE-MAP.md                     Outcomes, prerequisites, routes, and lab status
  GLOSSARY.md                       Definitions, examples, and counterexamples
  AGENTS.md                         A short agent entry point to the canonical course skills

  00_start_here/
  01_process_without_loops/
  02_loop_engineering/
  03_graph_engineering/
  04_ontology_engineering/
  05_system_intelligence/
  06_meta_harness_engineering/
  07_understanding_self_star/
  08_measuring_improvement/
  09_recursive_self_improvement/
  10_research_studio/
  11_capstones/

  skills/                           Canonical learner, builder, verifier, and research skills
  adapters/                         Agent-specific setup and capability checks
  examples/                         Small shared projects and public teaching fixtures
  research/                         Dated paper cards, claim checks, and source corrections
  assets/                           Original illustrations, diagrams, and verified charts
  instructor/                       Facilitation, misconceptions, solutions, assessment
  evidence/                         Sanitized, versioned validation records
  maintenance/                      Migration map, authoring rules, course validation
```

Each theme contains its own `README.md` and local lesson directories such as `step_01_why_repeat/`. Display IDs such as **02.01** make location and ordering obvious. Every page links to its theme, prerequisites, previous lesson, and next lesson.

A typical lab contains a README, a small starter brief, public example inputs, and relevant local assets. Shared skills and references are linked rather than copied into every lab. Detailed solutions live in the instructor area or a clearly marked reveal section. That is a teaching convenience, not a security boundary.

Generated work goes into a learner workspace outside the curriculum source. Each lab gets a clean starting checkpoint, a readable progress note, and a safe reset operation that affects only that lab's generated work. Course navigation and agent entry points remain consistent regardless of where the learner opens the agent.

## 4. The running project

Use **generic ML hill climbing on small tabular prediction tasks** as the main task class. Start with bike-demand regression. Add a wine-quality classification track to test which improvements transfer. Students train ordinary ML models; the coding agent writes the implementation. The task remains meaningful for an advanced AI/ML class while the introduction to harnesses and RSI starts from first principles.

The main dataset is [UCI Bike Sharing](https://archive.ics.uci.edu/dataset/275/bike+sharing+dataset). It contains hourly and daily rental counts with calendar and weather fields. The hourly CSV is about 1.1 MB. Predict the rental count for a specified information setting. Define that setting before selecting features: observed weather does not establish a realistic advance forecast. A forecast variant must use information available at its forecast origin.

The data also gives a concrete leakage lesson. The total count includes casual and registered users. Those component counts must not be inputs to a model intended to predict the total before those counts are known. Use a chronological split and train-only transformations. Freeze the final period before model selection. Record the actual downloaded file's row count, schema, license, version, and checksum rather than relying on a catalogue count.

For classification, use [UCI Wine Quality](https://archive.ics.uci.edu/dataset/186/wine+quality). It provides small CSV files of physicochemical measurements and quality scores. State the classroom label rule before evaluation, such as quality of at least 7. Explain that this binary label is our derived task. Inspect class balance, duplicates, and possible grouping before deciding the split. A threshold or split must never be chosen to flatter test performance.

Begin with a few rows that the student can inspect and a fixed train/validation/test protocol. Introduce a constant baseline, then a small linear or logistic model. Later compare bounded tree models and feature choices. Use MAE for the main regression objective, with supporting residual plots. For classification, choose the primary metric in the task brief, explain its tradeoff, and include class-wise errors. Accuracy alone must not hide a weak minority-class result.

| Course idea | What changes in the handbook task |
|---|---|
| A process | Inspect data, apply a fixed split, fit one baseline, and report its errors |
| A loop | Propose one feature or model change, evaluate it, and retain or reject it |
| A graph | Route missing-data issues, suspicious scores, and expensive candidates to different checks |
| An ontology | Connect datasets, columns, targets, feature rules, splits, experiments, models, metrics, and evidence |
| System intelligence | Coordinate data checks, experiment design, execution, error analysis, and independent evaluation |
| A meta-harness | Generate a runnable research workflow from a new prediction brief |
| Self-improvement | Retain a tested skill that improves later ML experiments |
| Recursive improvement | Revise the procedure that proposes and tests research skills; inherit and compare that revised procedure |

Hyperparameter search, feature search, and trying more models are ordinary optimization. They form the inner task. The course must show the additional step before calling an experiment recursive: a changed improvement procedure must govern later improvement work. Then compare that procedure with its predecessor under matched budgets on fresh tasks.

### Data science throughout the course

| Stage | What students inspect or decide | Readable result |
|---|---|---|
| Frame the problem | Prediction unit, target, information available at prediction time, useful metric, limits | Task brief |
| Acquire and document data | Source, permission, checksum, schema, units, provenance | Data card |
| Inspect the data | Types, missing values, duplicates, target distribution, class balance, time patterns | A short EDA report with plots |
| Design evaluation | Time or group boundaries, train/selection/test roles, leakage checks | Split report |
| Build a baseline | Constant predictor, then a simple model under the fixed split | Baseline report |
| Prepare features | Train-only transforms, encoding, scaling, availability of each field | Feature report |
| Run an experiment | Hypothesis, expected effect, one change, cost limit, actual outcome | Experiment note |
| Analyze errors | Residuals or confusion matrix, slices, failures, uncertainty | Error report |
| Retain or reject | Quality and resource checks; keep a failed attempt in the record | Decision and version history |
| Test generalization | Fresh tasks, frozen final test, repeated comparisons where justified | Evaluation report |
| Package the result | Model, transforms, data assumptions, reproducible local prediction | Model card and run instructions |
| Improve the research process | Edit proposal, diagnosis, allocation, or selection skills and test inheritance | Improver comparison |

These stages first appear as one simple pass. Later labs change one part at a time. The agent produces code, plots, and reports. Students predict, inspect, interpret, and explain. Missing-data exercises use clearly marked perturbed copies when the source data has no missing values. Keep the raw data unchanged.

No ordinary candidate may edit the target, metric, split, or protected test. A later lab can study a changed problem definition, but it starts a new evaluation record. An apparent gain from easier labels, leaked targets, more retries, or a weakened check is a finding to diagnose.

### From a laptop to a cluster

The laptop route uses small files, bounded CPU models, few candidates, and sequential execution. Set design targets of 8 GB RAM and no GPU, then validate them on an identified machine. Give measured times and resource use before calling a lab tested. Agent inference may run remotely. Its cost is separate from local model training.

Keep six concepts stable across scale: a task brief, a data version, an evaluator, a candidate, an improvement procedure, and a run record. A compute adapter executes a requested experiment and returns its artifacts and measurements. It must not redefine success.

Provide a progression from local CPU to local GPU, then a batch scheduler such as Slurm, and a cloud batch service where available. Students describe the backend, data location, model family, budget, and stop rules in plain language. The agent creates the launch files and configuration. Cluster credentials remain in the student's environment.

The larger-job path needs resumable trials, durable checkpoints, job IDs, bounded concurrency, timeouts, cancellation, retry rules, data staging, and a shared result store. Log failed and pre-empted jobs. Count GPU-hours, wall time, agent tokens, and monetary cost where available. A larger budget is a different comparison unless both methods receive it.

Teach synchronous search first. Introduce asynchronous selection only after students can explain completion-order bias, stale results, and unequal trial costs. Test the adapter contract locally with a small job; label GPU and cluster backends untested until they have real run evidence. Do not promise portability from generated launch files alone.

Later extension guides can use larger tabular data, neural models, or genuine model–harness co-evolution. They state resources and data assumptions and retain the same evidence rules. Scaling is a supported direction, not a claim that a laptop experiment establishes frontier-model RSI.

Research methods that need another task get small text or local-browser exercises, or an inspectable recorded experiment. Each lab explains what carries over to ML hill climbing and what does not. Adaptations remain clearly distinct from paper reproductions.

In the early course, **no loops** means no learner-designed retry, search, or improvement loop around the task. A coding agent may already use an internal tool loop, and a numerical library may iterate internally. This distinction must appear in the first theme.

## 5. The proposed lab sequence

### 00 — Start here: learn to observe before learning to optimize

| Lab | Student experience | Understanding to check |
|---|---|---|
| 00.01 | Meet the project, inspect a few inputs, predict one result | I understand the job before discussing AI machinery |
| 00.02 | Ask the agent to check its capabilities and prepare the workspace | I know what this environment can actually execute |
| 00.03 | Run a supplied one-attempt task | An agent's description and an executed result are different kinds of evidence |
| 00.04 | Inspect the output and explain how to recognize failure | A finished-looking answer needs a concrete success check |

### 01 — A process without loops

| Lab | Student experience | Understanding to check |
|---|---|---|
| 01.01 | Describe the job as a short sequence of actions | A process can be explicit before it is automated |
| 01.02 | Run that sequence once with a fixed recipe | Reproducibility starts with knowing what ran |
| 01.03 | Ask the agent to turn the process into a readable skill | A skill packages reusable instructions |
| 01.04 | Add one independent output check and a readable report | Instructions, tools, and checks play different roles |
| 01.05 | Repeat the same setup in a fresh session, without adapting it | Reuse of a fixed process does not itself change the process |

### 02 — Loop engineering

| Lab | Student experience | Understanding to check |
|---|---|---|
| 02.01 | Encounter a failure that motivates another attempt | Repetition needs a reason |
| 02.02 | Add a bounded retry with explicit state | A loop needs to know where it is and when to stop |
| 02.03 | Feed a concrete failure into the next attempt | Feedback must change an action to be useful |
| 02.04 | Add limits and detect repeated failures or oscillation | Continuing forever is not progress |
| 02.05 | Interrupt and resume from a checkpoint | A durable process can explain what has already happened |
| 02.06 | Compare fixed retries with feedback-guided revisions | A better task attempt and an improved task-solving system are distinct |

### 03 — Graph engineering

| Lab | Student experience | Understanding to check |
|---|---|---|
| 03.01 | Draw prerequisites between the actions already used | Dependencies explain execution order |
| 03.02 | Add a branch for two different input conditions | Different cases can need different routes |
| 03.03 | Split independent work and join its results | Coordination introduces information and failure-handling duties |
| 03.04 | Place a controlled retry inside the graph | A workflow may contain cycles; a DAG does not |
| 03.05 | Fail one node and resume the affected part | Recovery should follow the dependency structure |
| 03.06 | Compare the control graph, data flow, and execution trace | A picture of the plan and a record of what ran are different |

### 04 — Ontology engineering

| Lab | Student experience | Understanding to check |
|---|---|---|
| 04.01 | Name the domain's entities in a small Markdown table | Shared meaning prevents ambiguous instructions |
| 04.02 | Add relations among datasets, columns, splits, models, metrics, and evidence | A domain graph describes meaning and relationships |
| 04.03 | Express invariants in plain language and test examples | A valid-looking object can still be semantically wrong |
| 04.04 | Ask the agent to validate a deliberately inconsistent record | Domain rules become useful when they detect an actual mistake |
| 04.05 | Revise the vocabulary and trace the affected decisions | Ontologies change; their consequences should be inspectable |

Students distinguish an ontology, a taxonomy, a storage schema, a knowledge graph, and an execution graph. The course introduces only the machinery required by the examples; it does not impose a graph database or semantic-web stack.

### 05 — System intelligence

| Lab | Student experience | Understanding to check |
|---|---|---|
| 05.01 | Combine fixed skills, tools, and domain knowledge | Useful behavior can come from the system around a model |
| 05.02 | Route different tasks to suitable skills | Choosing a method is itself a system decision |
| 05.03 | Retrieve relevant reference knowledge and track task state | More context is useful only if the system can use it correctly |
| 05.04 | Coordinate planning, execution, checking, and escalation | Reliable work requires more than producing a proposal |
| 05.05 | Remove one component and compare the outcomes | We can investigate which component caused a benefit |

Here, system intelligence is a teaching label for coordinated system capability. It is not a standardized RSI level. These components remain fixed until later lessons explicitly introduce modification.

### 06 — A meta-harness generates a harness

| Lab | Student experience | Understanding to check |
|---|---|---|
| 06.01 | Describe the desired harness as a short goal and operating rules | A useful specification can be readable to a person |
| 06.02 | Invoke a builder skill to generate a first harness | A generator and its generated system have different responsibilities |
| 06.03 | Inspect the generated workflow, tools, checks, and limits | Generated output still needs inspection and execution |
| 06.04 | Run the generated harness and test an intended refusal | A written contract becomes credible through behavior |
| 06.05 | Generate a harness for a second task from a revised brief | The generator should adapt to the task rather than duplicate a template blindly |
| 06.06 | Compare generated harnesses and rerun from a clean environment | Generation alone establishes neither adaptation nor recursive improvement |

### 07 — Understand the self-* family through separate experiments

| Lab | Student experience | Understanding to check |
|---|---|---|
| 07.01 | Correct an answer within one task | Self-correction can be temporary |
| 07.02 | Reflect on an attempt, then test whether the reflection helps | A plausible explanation is not necessarily a useful lesson |
| 07.03 | Retain a validated lesson and apply it in a later task | Persistent learning changes future behavior; describe exactly what changed |
| 07.04 | Improve a task skill using a fixed improvement procedure | A system can improve while its improver remains fixed |
| 07.05 | Let roles or routing reorganize under explicit local rules | Self-organization concerns organization and need not improve capability |
| 07.06 | Observe a collective behavior and test its dependence on local interactions | Emergence concerns how behavior arises; it does not require an unwritten rule or imply improvement |
| 07.07 | Use self-play to generate practice and assess transfer | Generating experience is separate from benefiting from it |
| 07.08 | Compare self-modification, self-evolution, learning, and the previous experiments | These terms describe different dimensions, not a universal staircase |

“Self-emerging” will be identified as imprecise language and unpacked into the actual mechanism being claimed. Definitions will always include an example, a near miss, and the evidence needed to distinguish them.

### 08 — Measure improvement before claiming recursion

| Lab | Student experience | Understanding to check |
|---|---|---|
| 08.01 | Establish a fixed baseline and repeat runs | A single lucky result can mislead |
| 08.02 | Separate development feedback from a final evaluation | Reusing evaluation feedback changes what the evaluation means |
| 08.03 | Match resource budgets and record research overhead | More resources can explain an apparent improvement |
| 08.04 | Disable memory, policy changes, or other interventions separately | Ablations help attribute changes to mechanisms |
| 08.05 | Freeze a candidate and test fresh tasks and distributions | Training success and transfer success are separate claims |
| 08.06 | Demonstrate a misleading metric, detect regression, and roll back | A successful rejection is part of a reliable improvement system |

### 09 — Recursive self-improvement

| Lab | Student experience | Understanding to check |
|---|---|---|
| 09.01 | Identify the task solver, the improver, and the protected evaluation | We must say which system component is the “self” |
| 09.02 | Run multiple improvements with an unchanged improver | Repeated self-improvement establishes the comparison baseline |
| 09.03 | Use evidence to propose a change to the improvement procedure | The target of change now includes how future improvements are made |
| 09.04 | Inherit and invoke that revised procedure in a later improvement round | A recorded modification must actually govern later work |
| 09.05 | Compare original and revised improvers from comparable starting states | Better current task performance is not enough to establish a better improver |
| 09.06 | Run bounded generations with checkpoints, rejection, and stopping | Lineage, costs, failures, and retained changes must remain visible |
| 09.07 | Classify what the experiment supports and what remains unproved | Structural recursion, effective improvement, and accelerating progress require different evidence |

This completes an executable bounded recursion workflow. Its measurement may show success, failure, or uncertainty. General autonomous RSI and sustained acceleration remain research questions to examine, not promised classroom outcomes.

### 10 — Research studio: rebuild the mechanisms and read the evidence

This theme expands into a substantial advanced course. Each named system gets the space needed to understand its mechanism, construct an affordable experiment, and interpret the evidence. Its directories are thematic too:

```text
10_research_studio/
  README.md
  00_reading_frontier_research/       Labs 10.01–10.02
  01_memory_and_exploration/          Labs 10.03–10.06
  02_dream_rsi/                       Labs 10.07–10.09
  03_modular_harness_evolution/       Labs 10.10–10.12
  04_aide2/                          Labs 10.13–10.15
  05_meta_skill_evolution/            Labs 10.16–10.17
  06_scientist_two/                   Labs 10.18–10.21
  07_sciencebuddy/                    Labs 10.22–10.26
  08_skills_and_procedures/           Labs 10.27–10.29
  09_efficient_harnesses/             Labs 10.30–10.31
  10_feedback_and_transfer/          Labs 10.32–10.34
  11_evidence_and_open_questions/     Labs 10.35–10.36
```

| Lab | Focus | Student task |
|---|---|---|
| 10.01 | The September RSI framework | Apply its criteria to a mechanism students already built |
| 10.02 | Frontier-lab announcements and researcher threads | Trace a claim from its original announcement to the available evidence |
| 10.03 | RSIAgent: exploration | Choose broad exploration tasks, then investigate a specific uncertainty |
| 10.04 | RSIAgent: outcome verification and memory | Inspect actor-authored lessons after a verifier checks the outcome |
| 10.05 | RSIAgent: frozen-memory evaluation | Freeze learning and compare against a memory-free baseline |
| 10.06 | Recuris | Compare current working state with reusable experience |
| 10.07 | Dream-RSI: discovery trees | Build and inspect a small history of attempted solutions |
| 10.08 | Dream-RSI: replay | Compare exploration policies using recorded outcomes and identify missing coverage |
| 10.09 | Dream-RSI: return online | Test the selected policy on new work and account for total cost |
| 10.10 | ModularRSI: localizing a problem | Use contrasting outcomes to propose a restricted module edit |
| 10.11 | ModularRSI: integration and transfer | Combine checked edits and assess unseen tasks |
| 10.12 | DGM and HyperAgents | Compare agent lineage with changes to the improvement procedure |
| 10.13 | AIDE²: inner research | Inspect search operators and candidate selection |
| 10.14 | AIDE²: outer research | Compare inner-researcher revisions under a total budget |
| 10.15 | AIDE²: ignition | Test whether a better inner researcher is a better outer improver |
| 10.16 | MetaSkill-Evolve: task skills | Run a fixed improvement pipeline and inspect its limitations |
| 10.17 | MetaSkill-Evolve: meta-skills | Change the improvement pipeline on a slower schedule and evaluate inheritance |
| 10.18 | ScientistTwo: from problem to hypothesis | Establish a baseline and propose testable explanations for its limitations |
| 10.19 | ScientistTwo: screening and ablations | Screen ideas cheaply, then test the contribution of each component |
| 10.20 | ScientistTwo: review and rebuttal | Turn a reviewer criticism into a new experiment and an evidence-based response |
| 10.21 | ScientistTwo: successive discoveries | Reuse a result as a baseline and audit what actually improved |
| 10.22 | ScienceBuddy: researcher interaction | Turn a supplied request, artifact, and correction into a task and rubric |
| 10.23 | ScienceBuddy: harness adaptation | Revise procedures while holding model weights fixed |
| 10.24 | ScienceBuddy: GRPO foundations | Inspect rollout groups and rewards; run a tiny numerical update demonstration and explain what real LLM training adds |
| 10.25 | ScienceBuddy: coupled cycles | Use recorded results to track model–harness pairs; run a labeled small simulation of the cycle |
| 10.26 | ScienceBuddy: result audit | Distinguish single-attempt accuracy, multi-attempt coverage, and reported feedback sources |
| 10.27 | WikiSkill | Keep raw traces, a knowledge notebook, and active skills separate; reject a skill edit while retaining the lesson |
| 10.28 | Procedural Graphs | Refine a small procedure graph from successes and failures; compare selection results with a fresh test |
| 10.29 | EvoSkill-GUI | Repair a skill for a local experiment-results page; inspect what an independent critic can see |
| 10.30 | SoL-Pi | Compare a few harness changes for research cost and predictive quality under fixed acceptance rules |
| 10.31 | HarnessDev and Harness-of-Harness | Generate a small harness, improve it, and test transfer; separate improved task outputs from improved infrastructure |
| 10.32 | S3Gym | Compare raw history with summarized memory on a tiny text task with an executable checker |
| 10.33 | Environments as Scaffold | Compare action hints with richer observations; remove the help for the final check |
| 10.34 | Model–harness fit | Audit the on-policy correction study; run a small interface-mismatch experiment without claiming weight training |
| 10.35 | Cross-system comparison | Identify mutable components, retained mechanisms, human roles, and evaluation boundaries |
| 10.36 | Economics and open questions | Examine costs, bottlenecks, uncertainty, and claims of acceleration |

The foundation themes are prerequisites. Add just-in-time primers for scientific hypotheses, ablations, peer review, reinforcement learning, and GRPO. Explain GWAS and the other scientific task families using simple read-only examples before expecting domain understanding. A student should understand the question an experiment asks before encountering a training objective or specialist acronym.

Each advanced lab includes original diagrams, exact skill-based prompts, a runnable mechanism exercise, an artifact to inspect, a source-and-simplification map, and its own quiz with explained answers. Architecture diagrams explicitly mark what changes and what remains fixed. Attribution cards identify authors, institutions, publication/version date, paper, official project, and repository. Figure reuse requires checking licensing; original explanatory redrawings carry citations.

Every required advanced lab has a laptop-sized activity. Use a live mechanism experiment where feasible. For GPU-dependent methods, combine an executable small demonstration with an audit of published results or authentic released artifacts. A numerical demonstration of an update is not GRPO training of an LLM. A prompt edit is not a weight update. A replay is not a new experiment. State the distinction beside the action, before students run it.

Full foundation-model training and full-scale paper reproduction are outside the required laptop route. Add extension guides for students with suitable GPUs or clusters, including genuine model training where the source method needs it. Keep the same task and evidence interfaces. State code availability, data access, resources, and reproduction limits before a run. The agent generates implementation and configuration; students never need to handwrite them.

The paper audits already reveal useful teaching distinctions:

- [ScientistTwo](https://arxiv.org/html/2609.19644v1) evaluates research artifacts with automated reviewers. Their acceptance scores are not actual conference acceptance decisions. Repeatedly improving a scientific solution also needs a separate audit before classifying it as improvement of the researcher itself.
- [ScienceBuddy](https://arxiv.org/html/2609.17523v1) reports 42.2% to 73.3% held-out single-attempt accuracy over three coupled cycles. Its reflector stays fixed. Real researcher interactions, simulated procedural feedback, and rubric-derived GRPO rewards must be distinguished in the explanation.
- [RSIAgent](https://arxiv.org/html/2609.15364v1) uses outcome verification followed by actor-owned memory updates. The verifier does not author or approve the wording of that memory. This corrects an important mismatch with the existing course's verifier-written memory example.
- [Dream-RSI](https://arxiv.org/html/2609.14858v1) replays the recorded discovery structure; the classroom exercise must make its coverage and online confirmation explicit.

### 11 — Capstones and teach-back

| Lab | Deliverable | Acceptance |
|---|---|---|
| 11.01 | A harness generated for a new brief | Another learner can run and inspect it |
| 11.02 | A bounded recursive improvement experiment | Its lineage shows inherited improver changes and fair comparisons |
| 11.03 | A transfer and portability study | It distinguishes task transfer from agent/runtime compatibility |
| 11.04 | An audit of someone else's RSI claim | Conclusions match the strength and limitations of the evidence |
| 11.05 | A small teaching portfolio | The student explains every layer, including a failure and a counterexample |

## 6. The main README experience

The top-level README will provide enough context to understand the course before opening a lab. It will have a designed reading arc:

1. A simple opening question: **Can we build a system that becomes better at improving itself?**
2. A friendly illustration of the project and the artifacts students will build.
3. A concrete ordinary workflow, showing where its limitations appear.
4. A visual journey through the twelve themes, with one sentence explaining the purpose of each.
5. A clear statement of what students do and what the coding agent does.
6. A first successful action reachable after a short introduction.
7. A course map with prerequisites, outcomes, measured duration/cost information when available, and direct links.
8. Guidance for self-study, classroom use, restarting, and asking for help.
9. A brief research context and freshness date, with detailed paper cards linked nearby.
10. A clear picture of what a successful final project contains.

The README will tell a coherent story while leaving detailed contracts and execution transcripts beside the lessons that need them. Typography, whitespace, diagrams, and tables will carry the hierarchy. Decorative badges and large configuration dumps will not carry the explanation.

Theme READMEs answer: What can I already do? What new problem will I meet? What will I build here? Why does the next theme become useful?

## 7. The lab teaching pattern

Every lab follows a small, repeatable learning cycle:

**Recall → encounter a problem → predict → act → observe → explain → change one thing → check understanding.**

Each lab README must stand on its own after its stated prerequisites. It explains what to run, what the run does, why the idea matters, and how the method addresses the problem. It must not depend on a previous chat or an unwritten instructor explanation. Step durations and clear outcomes follow the spirit of the [Google Codelabs format guidance](https://github.com/googlecodelabs/tools/blob/main/FORMAT-GUIDE.md). Calibrate time estimates through actual walkthroughs.

Use simple, descriptive sections in this order. Short labs can combine related sections without losing their content.

1. **What you will build.** Show a concrete input and output. State the one new idea.
2. **Why this matters.** Show the limitation of the previous method and the cost of leaving it unchanged.
3. **Before you start.** Give prerequisites, exact starting files, supported agent capabilities, setup steps, and known resource needs.
4. **How it works.** Explain the mechanism with a small example and an original diagram. Define each new term before using it.
5. **Run the lab.** State where to open the agent and which folder it must use. Give complete copyable prompts, one step at a time. Explain each prompt before the student runs it.
6. **Check your result.** Show which file to open, what to look for, and what counts as success. Label example output separately from output produced by the student's run.
7. **Try one change.** Ask for a prediction, change one condition, and compare results. Use a counterexample to expose the limit of the idea.
8. **If something goes wrong.** Describe likely symptoms, checks, recovery, stop, resume, and reset steps.
9. **Key takeaways.** Give three to five concrete lessons tied to the observations. Include where the idea stops being useful.
10. **Check your understanding.** End with a short quiz and explained answers in a reveal section.
11. **What's next.** Name the remaining problem, explain why the next lab addresses it, and link directly to that lab.

Each run step pairs four things: the action, its purpose, the expected observation, and the response to an unexpected result. “Run the skill” is insufficient without a verified skill entry point, starting state, and result check. A clean-session walkthrough must establish that the instructions work.

### Writing that is easy to follow

Use [ASD-STE100](https://www.asd-ste100.org/) as the technical writing reference. Its controlled-language rules and dictionary need a separate conformance review before any formal compliance claim. The course's editorial rules are concrete:

- Use one action per instruction and one main idea per sentence. State conditions before the action they control.
- Prefer active voice, direct verbs, short paragraphs, and familiar words. Aim for short sentences; review long sentences instead of splitting them mechanically.
- Use one term for one concept. Keep a course glossary for technical names such as harness, ontology, and recursion. A simpler synonym must not change the meaning.
- Explain the example first. Introduce the formal name after students can see what it describes.
- Address the student directly and respectfully. Avoid hype, filler, manufactured excitement, repeated summaries, and claims that an idea is “obvious” or “easy.”
- Use headings that say what the section contains. Avoid slogans, decorative badges, ornamental dividers, catchphrases, and generated author or tool footers. End with useful navigation.
- Use a literal explanation after an analogy. State where the analogy breaks down.
- Read each lesson aloud during editorial review. Check whether a beginner can explain its purpose and predict a new case without repeating the wording.

For example: “The model makes larger errors during rush hour. Trying it again with the same inputs may not help. First, inspect those errors. Then test whether an hour-of-day feature reduces them on later data.”

### Ideas students can use again

For every lab, define the intended mental model, the common misconception, an observation that separates them, and a transfer question. These guide the author; they do not need four extra headings in the student page.

Revisit the idea in later labs. Ask students to draw the mechanism from memory, explain a failed run, or predict what happens when one component is removed. A good takeaway explains a cause or a limit: “A retry needs useful feedback,” rather than “You learned loop engineering.” A good next-step paragraph exposes the next problem: “One candidate failed its data check. Another passed, but took too long to train. They need different next steps. In the next lab, you will add a branch.”

The course skill guides the learner one step at a time. It does not race through the whole lesson and reveal every answer. Hints escalate gradually. The student can ask “Explain that more simply,” “Show what changed,” or “Help me check my result.”

Example teaching sequence:

> Yesterday, the agent used a checklist to try improvements. Today, we let it change that checklist. Has it become a better improver?
>
> Not enough information yet. Give the old and new checklists the same starting project and the same budget. Now compare the improvements they produce. Finally, confirm that the next generation actually uses the revised checklist.

Useful moments of discovery are deliberately placed throughout: a retry repeats the same mistake; a branch avoids an irrelevant tool; an ontology catches a mismatch; a memory helps one case but harms another; a changed score comes from extra compute; an improved solver fails to improve its successor.

Basic evidence vocabulary appears early. Formal statistical analysis, paper taxonomies, and recursive evaluation arrive only after concrete examples.

### A quiz at the end of every codelab

Every one of the proposed 99 labs ends with a short quiz, usually four to six questions, followed by “What's next.” The opening labs use simple language and brief answers. Later labs include traces, diagrams, experimental comparisons, and claim audits.

Each quiz combines concept recognition, interpretation of the actual lab result, a prediction about changing one condition, and a short explanation in the student's own words. Selected labs add a debugging or transfer question. Multiple-choice questions use plausible misconceptions as distractors and explain why each answer is right or wrong. Questions never depend on memorizing JSON keys, Python syntax, or paper names.

For example, the first persistent-memory lab might ask:

1. What survived when you started a new session?
2. What observation shows that the agent actually used it?
3. If the memory file grew but performance stayed the same, what could you conclude?
4. Does this result establish that the improvement procedure became better? Explain.

Answers and reasoning are available in a clearly marked reveal section, with instructor notes for open-ended answers. The agent tutor waits for the student's attempt, offers progressively more specific hints, checks reasoning against a rubric, and connects a mistake to the relevant step. A learner may choose to reveal an answer or move on; the record distinguishes demonstrated understanding from skipped or revealed questions.

Quizzes are formative learning checks, separate from the automated checks that establish whether the generated system works. Theme-level reviews revisit earlier concepts in new situations. Capstones require a teach-back so that executing the agent's instructions alone is insufficient to demonstrate mastery.

## 8. Illustrations and visual standards

The requested generator is **Imagen 2.5**. Use a white background, professional composition, careful spacing, and rich but readable detail. A viewer should see the main causal idea before reading the caption. The currently available image tool has no Imagen 2.5 model selector. Verify access to the requested generator before production; do not silently substitute a model or claim that it was used.

The visual system uses consistent shapes, labels, and colors for the learner, host agent, task harness, improver, tools, evidence, and protected evaluator. Color is reinforced by labels and shapes.

Give each illustration one main question to answer. Use a clear reading path, numbered stages where helpful, short labels, and meaningful arrows. Show inputs, outputs, changing components, fixed components, and evaluation boundaries. A detailed overview may use panels; an introductory explanation still reveals one new mechanism at a time. Detail must not make labels too small to read.

Review generated images for incorrect arrows, missing steps, misleading boundaries, spelling, duplicated elements, and unsupported claims. Retain the prompt and a short review note with each asset. Render measured plots from actual run data with plotting tools. An illustration generator must not invent experimental curves, scores, or evidence.

| Visual | Where it appears | What it must make clear |
|---|---|---|
| An approachable project illustration | Main README and onboarding | The student can see the job and tangible outputs |
| One evolving architecture diagram | Across themes | Only the newly introduced mechanism is highlighted |
| A loop with actual state changes | Loop engineering | Attempt, check, revise, stop, and resume are different events |
| A dependency graph beside a run trace | Graph engineering | Planned paths and executed paths can differ |
| A concept map beside an execution graph | Ontology engineering | Meaning and execution order are different relationships |
| A harness generator with a visible generated package | Meta-harness theme | The builder and the thing built are separate systems |
| Small side-by-side examples | Self-* theme | Similar words can refer to different mechanisms |
| Nested loops and a generation timeline | RSI theme | The revised improver is inherited and used later |
| A candidate/evaluator boundary | Measurement and advanced labs | Which information and permissions cross the boundary |
| Cost, quality, and uncertainty charts | Measurement and capstones | The reported result comes from identifiable run evidence |
| A paper mechanism diagram with marked simplifications | Research studio | The classroom exercise's relationship to the original system |

Use Mermaid or SVG for precise technical diagrams; export a static alternative where rendering support requires it. Use original raster illustrations where an analogy materially improves understanding. Any generated illustration gets a technical accuracy review. Scientific plots are generated from actual data, with illustrative data conspicuously labeled if used before live runs.

Store assets in the repository, embed them directly in Markdown, supply captions and alt text, and check readability in GitHub light and dark modes, at narrow widths, and at ordinary zoom. Prefer original redrawings with citations over copying paper figures without checking their license. Meaning must also remain available in prose.

## 9. How the skills become executable

The architecture separates five responsibilities:

| Responsibility | What it does |
|---|---|
| Learner guide | Loads the chosen lab, guides a step, offers hints, records a checkpoint |
| Builder skill | Converts readable goals and operating rules into tools and a runnable harness |
| Execution environment | Runs the generated work and records actual outcomes and resource use |
| Evaluator | Checks outputs against stable criteria through a declared information boundary |
| Research auditor | Connects claims to sources and distinguishes demonstrations from reproductions |

Example learner requests are deliberately ordinary:

```text
Read START-HERE.md and help me run my first lab, one step at a time.

Start lab 02.03. Explain the new idea before we run it.

Show me what changed from the previous lab and why it matters.

Check my result against this lab's checkpoint. Give me a hint if I missed something.
```

Skill files use the minimal metadata required by the relevant specification; the agent manages it. Required schemas and machine configuration remain implementation artifacts. They may be inspected in an optional technical explanation but are never a prerequisite for typing the learner instructions. The [Agent Skills specification](https://agentskills.io/specification) provides a useful portable packaging baseline, with detailed resources loaded as needed.

A canonical skill source prevents independent copies from drifting. Agent-specific installation, discovery, hooks, and tool integrations are projections maintained by the bootstrap process. An agent without native skill discovery can be instructed to read and follow the same entry files if it has the necessary tools.

Portability has levels: instructions readable; tools executable; integration tested; evaluation boundary supported. Claude Code, Codex, and at least one additional available agent are validation targets. An unavailable runtime is recorded as untested. The course must not claim universal execution or equivalent isolation from a shared file layout alone.

Generated tools are versioned and checked before comparisons. Control and treatment share the same fixed implementation except for the intended intervention. A contract written by the candidate is not sufficient evidence that a restriction holds.

## 10. Evidence and evaluation design

Evaluation becomes progressively stronger as the course develops. The initial lessons use transparent public fixtures so a novice can understand every step. Later experiments distinguish:

- Public practice cases and development feedback used for improvement.
- Selection cases used to decide among candidates, whose feedback may itself be overfit.
- Fresh final evaluation cases held outside the candidate's accessible context and tools.
- Transfer cases testing a different task distribution or domain.

A file named “private” inside the same accessible repository is not a private holdout. Stronger labs require an instructor-controlled evaluator, an isolated execution environment, or another technically verified boundary. If the available adapter lacks this boundary, its result remains a classroom demonstration and the limitation is explicit.

The improver may not silently weaken the protected final acceptance rule. Advanced evaluator-evolution exercises use separately anchored tests and versioned evaluation epochs. Approval and freeze checks refer to the exact action and artifact, not to any matching file in a directory.

Every advanced experiment records its starting state, candidate change, model and agent versions, data split, evaluator version, resource budget, complete set of attempts, rejected candidates, retained successor, and terminal reason. It keeps enough evidence to rerun and audit the result.

Resource accounting includes candidate generation, evaluation, retries, and failed proposals. When token, price, or compute measurements are unavailable, report the available measurement and its limits; do not equate a fit count with equal total research expenditure.

Report repeated trials and uncertainty where meaningful. Avoid cherry-picked seeds or silently dropping failed runs. Test that retained changes are actually activated. A memory-off experiment is an attribution tool, not a universal proof of RSI.

## 11. Research program and initial verified reading set

The research process will search official lab publications, arXiv, author repositories, relevant established venues, and original researcher posts and threads on X/Twitter. This explicitly includes Meta/FAIR researchers and other authors who publish early findings or technical details through social posts before a paper exists. A source's reputation helps prioritize reading; it does not substitute for examining its methods. Preprints, company self-reports, independently reproduced results, theoretical proposals, and post-only announcements receive different labels.

For each included work, read the relevant full text, methods, appendices, evaluation protocol, ablations, and limitations. Inspect released code, datasets, license, and reproduction instructions. Record first publication and revision dates separately. Save a readable paper card containing the claim, mechanism, mutable component, fixed components, evidence, costs, limitations, and planned lesson connection.

For social-first work, verify the account's identity and affiliation, retain the canonical post URL and date, read the complete relevant thread, and follow linked papers, repositories, demos, and corrections. A post can be the primary source for what an author announced, even when no paper exists. Its empirical claim is labeled according to the evidence actually accessible. Search snippets, reposts, engagement counts, and screenshots without a verified origin do not substitute for the original source. If access fails, record that limitation rather than inventing the thread's contents. Expand paper cards into research cards so social-first work has a first-class place in the course.

All further discovery queries target **20 August–19 September 2026** using explicit date terms and the available recency filter. Prioritize the latest two weeks. Verify each result's first publication and revision dates on its primary source: a recent crawl or repost does not make a paper recent. Recheck at implementation start and before delivery, recording the new cutoff. Older necessary work belongs in a separate foundations list. The [research inventory](RSI-RESEARCH-SWEEP.md) contains the broader sweep and reading status; the table below preserves the originally required sources.

| Source | Date/version checked | Planned teaching role |
|---|---|---|
| [The Last AI Built by Humans: Toward Genuine Recursive Self-Improvement](https://arxiv.org/abs/2609.11873) | First submitted September 10; v2 September 15 | Autonomy, inherited mechanisms, and the distinction between structural and effective recursion |
| [Dream-RSI](https://arxiv.org/abs/2609.14858) | September 14 | Exploration policy improvement using historical discovery trees |
| [ModularRSI](https://arxiv.org/abs/2609.14857) | September 14 | Restricted module changes, contrasting trajectories, and evaluation on unseen tasks |
| [RSIAgent](https://arxiv.org/abs/2609.15364) | September 14 | Environment exploration and verified persistent memory |
| [ScienceBuddy](https://arxiv.org/abs/2609.17523) | September 15 | Coupled harness evolution and model learning |
| [ScientistTwo: Pioneering the Human Knowledge Frontier with Autonomous AI](https://arxiv.org/abs/2609.19644) | September 17 | Autonomous scientific investigation, ablations, review/rebuttal, and research-artifact auditing |
| [The Economics of Recursive Self-Improvement](https://arxiv.org/abs/2609.15802) | September 14 | Feedback bottlenecks and the distinction between narrow gains and broader acceleration |
| [Research acceleration: The view inside OpenAI](https://openai.com/index/research-acceleration-view-inside-openai/) | September 6 | Internal research-assistance measurements and their methodological limitations |
| [An Alien Mind](https://openai.com/index/an-alien-mind/) | September 6 | A frontier-lab perspective; distinguish expectations from published experimental evidence |
| [Measurements for understanding the pace of AI development inside frontier labs](https://www.anthropic.com/institute/measuring-pace-of-ai-development) | Listed by Anthropic on September 17 | Separate automation, oversight, and compute measurements |
| [When AI builds itself](https://www.anthropic.com/institute/recursive-self-improvement) | Includes a September 18 update; original date to verify | Compare internal evidence and forecasts with classroom claims |
| [AIDE²](https://www.weco.ai/blog/first-evidence-of-recursive-self-improvement) | July 14; essential earlier work | Nested research optimization and the separate ignition test |
| [MetaSkill-Evolve](https://arxiv.org/abs/2607.05297) | July 6; essential earlier work | Changes to both task skills and the procedure that improves them |
| [Recuris](https://arxiv.org/abs/2608.24876) | August 25; within the one-month window | Working memory, experience, and the role of a fixed meta-agent |

Broaden the search across Google/DeepMind, OpenAI, Anthropic, Meta, Microsoft Research, and other research groups with relevant primary publications. Include findings for relevance and evidence quality rather than assigning a quota to each institution. Verify older lineage references such as STOP, DGM, and HyperAgents directly before writing their lessons.

Two important research checks are already concrete. Weco's AIDE² report separates its claimed improvement results from an ignition test that it says did not establish statistically significant superiority of the evolved outer improver. Its level numbering must remain separate from the survey's autonomy framework. Also, the [Dream-RSI repository](https://github.com/zhengkid/Dream-RSI) currently says its code is being prepared for release, so the course must distinguish a paper-inspired exercise from a released-code reproduction.

## 12. Implementation order and reviewable outputs

| Phase | Work | Evidence required to proceed |
|---|---|---|
| A. Complete the audit | Review all current lesson packs and their tests; reconcile transcript claims with primary sources; map reusable material | A source correction ledger, a migration map, and a test-discovery impact record |
| B. Establish the teaching design | Finalize outcomes, prerequisite graph, terminology, running project, README storyboard, and visual language | Every lab has a reason to exist and a concrete checkpoint |
| C. Build representative lessons | Produce onboarding, one loop lab, one ontology lab, and the critical self-improvement-to-RSI transition | A newcomer can follow the prompts; runtime evidence supports the claims; visual explanations survive review |
| D. Build foundations | Complete themes 00–06 with skills, tools, illustrations, checkpoints, and navigation | Clean-session runs and deliberate failure checks pass on the primary agent |
| E. Build improvement and recursion | Complete themes 07–09 and their comparisons | Persistence, inheritance, evaluation boundaries, rejection, rollback, and budget stops are demonstrated |
| F. Build the research studio | Read and map papers in depth; build laptop-sized experiments and published-result audits | Each research claim has a source; each activity runs within its stated budget and explains what it omits |
| G. Build capstones and instructor support | Add assessment, troubleshooting, hint ladders, solutions, and teaching notes | Students must explain mechanisms, interpret evidence, and handle a failed experiment |
| H. Validate and migrate | Run agent compatibility checks; update root navigation and test discovery; replace old entry points with a migration guide | Every lab is reachable, every asset resolves, claimed compatibility has run evidence, and unrelated series still pass their checks |

The first implementation batch should make the editorial and technical standard visible through representative working lessons before scaling that pattern across the course. This is a production checkpoint, not a substitute for completing the remaining course.

## 13. Acceptance criteria

The rebuilt course is ready only when all of the following are true:

- A student can start with no RSI knowledge and complete the initial lab without writing implementation code or machine configuration.
- Every new term is explained before use, with a concrete example and a relevant counterexample.
- The required sequence from ordinary process through loops, graphs, ontology, system intelligence, meta-harnesses, self-* distinctions, and RSI is intact.
- The top-level README and every theme README provide context, direction, and useful links.
- Every lab explains its purpose, context, approach, and prerequisites. It provides complete run instructions, exact prompts, an observable result, troubleshooting, a checkpoint, key takeaways, a quiz with explained answers, a restart path, and “What's next.”
- Every required lab has a laptop-sized activity with declared and tested resources. No required lab trains a foundation model or needs a GPU cluster.
- Data acquisition, EDA, leakage checks, split design, baselines, features, model selection, error analysis, and final evaluation appear in the running ML project.
- The main task supports both regression and classification. Ordinary model optimization is clearly distinguished from improving the procedure that conducts that optimization.
- A documented compute adapter supports future scale-up. Tested backends have run evidence; other backends have explicit status. Larger budgets never silently stand in for better improvement methods.
- Editorial review checks short, direct instructions, consistent terms, descriptive headings, and unnecessary repetition. A glossary and a conformance review support any formal ASD-STE100 claim.
- Students can explain why the mechanism works, identify a case where it fails, and apply the idea to a new example. Completing the steps alone does not establish understanding.
- Images and diagrams are technically accurate, legible, accessible, locally stored, and embedded beside the explanations they support.
- Students can distinguish a workflow graph from an ontology and can explain the course-specific use of system intelligence.
- Students can distinguish correction, reflection, learning, improvement, organization, emergence, self-play, modification, and recursive meta-improvement.
- A generated harness executes; a written tool contract alone is insufficient.
- Behavior tests exercise actual failures and refusals rather than only checking document wording.
- Candidate and evaluator information boundaries are demonstrated or honestly marked as unsupported.
- The recursion capstone records a revised improvement procedure governing a later round and compares its effectiveness fairly.
- Research adaptations, full reproductions, reported results, and classroom measurements are visibly distinguished.
- All agent/platform support claims are tied to versions and observed tests; unavailable runtimes remain marked untested.
- All named papers and researcher posts have verified citations, dates, mechanism descriptions, and limitations; the latest source sweep is dated and post-only claims are labeled.
- The repository's root navigation and validation tooling discover the new thematic structure.
- No claims of success depend on invented transcripts, guaranteed improvement, or a model's unverified self-assessment.

## 14. Scope and present status

The repository has been cloned under the current workspace's `work/simple-coding-harness` directory. The original MHTML has been decoded locally for inspection. Neither the transcript nor its incidental personal details will be copied into the public curriculum.

The proposed change covers the RSI course and the repository integration required for its themed layout. The other tutorial series remain outside the curriculum rewrite. Existing history remains recoverable through Git, with a readable old-to-new lesson map.

This file is the planning deliverable. Course implementation has not started and no live course runs have been claimed. The user authorized GitHub checkpoints of the plans and process notes. Keep those records under `how-did-i-generate-it/rsi/` on the working branch. The next course step is the user's review of this blueprint.

Checkpoint after meaningful milestones: update the steering record and work log, inspect the diff, run checks appropriate to the changed files, commit, push, and verify the remote commit. Never describe a local commit alone as a GitHub backup. Do not store credentials, raw private transcripts, or unsupported completion claims in the public record.
