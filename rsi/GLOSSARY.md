# A glossary you can use while learning

[Course](README.md) · [Teaching roadmap](TEACHING-ROADMAP.md) · [Every lab](COURSE-MAP.md)

Start with the words needed for your current experiment. You do not need to memorize this page. Definitions use the course's small ML project. A research paper may use a different definition; keep its meaning beside its claim.

| Find a term about… | Go to… |
|---|---|
| The main course concepts | [Quick definitions](#quick-definitions) |
| Data, models and predictions | [One experiment](#one-experiment) |
| Files, state and agent operation | [Working with an agent](#working-with-an-agent) |
| Revisions and evidence | [Following a change](#following-a-change) |
| Research and larger jobs | [Research and compute](#research-and-compute) |
| Easily confused ideas | [Distinctions that matter](#distinctions-that-matter) |

## Quick definitions

Read the definition, then test it against the example. “What changed?” and “What evidence supports that?” are useful questions for every row.

| Term | Meaning here | Example or counterexample |
|---|---|---|
| Task model | A fitted regressor or classifier | The bike-demand linear model |
| Baseline | A simple, declared starting method used for comparison | Predict the training median every hour |
| Mean absolute error (MAE) | Average absolute difference between predictions and outcomes | An error of 10 means ten rentals per hour in this task |
| Balanced accuracy | Mean recall across classes | A majority-only binary classifier scores 0.5 when both classes occur |
| Leakage | Evaluation or outcome information enters a place where the prediction contract forbids it | Using the two counts that sum to the target |
| Hill climbing | Propose a change, evaluate it, and retain eligible improvements | Change a feature group while preserving the evaluator; it can stall or overfit |
| Coding agent | A language model operating with instructions, tools, and state | The agent that generates an experiment |
| Skill | A reusable written procedure read by an agent | Inspect error slices before proposing a change |
| Tool | An executable operation | Fit one recipe and save predictions |
| Harness | Organized instructions, tools, state, checks, and limits around execution | A bounded ML workflow |
| Meta-harness | A procedure that generates a harness from a brief | A task-specific harness builder |
| Process | A sequence or structure of actions | Inspect, split, fit, check, report |
| Loop | Repetition with state and an exit condition | Try at most three candidates |
| Execution graph | Dependencies and routes among actions | Invalid data goes to repair before fitting |
| Ontology | Domain concepts, relations, and constraints | Models use features; target-derived inputs are invalid here |
| Taxonomy | A classification of types | Regression and classification under supervised learning |
| Storage schema | The structure of stored records | Required fields in a candidate record |
| Knowledge graph | Concrete entities and relation facts using a vocabulary | Candidate A uses dataset version B |
| System intelligence | Course term for capability of coordinated components | Not a standard RSI level |
| Self-correction | Revising a current output | Correcting a report without saving a new procedure |
| Reflection | Interpreting experience to propose a lesson | A hypothesis about why a candidate failed |
| Learning | Retained adaptation that can affect later behavior; name the mechanism | Memory, skill edits, and parameter updates differ |
| Self-improvement | Retained system change with demonstrated relevant benefit | A better task skill under a fixed improver |
| Self-organization | Changed arrangement or coordination under system rules | Dynamic work redistribution, possibly without a gain |
| Emergence | A specified collective pattern arising through interactions | Not automatic evidence of intelligence |
| Self-play | Experience from playing against system versions or from coupled challenge generation and solving | A proposer–critic exchange alone does not demonstrate self-play training; agreement is not ground truth |
| Self-modification | Editing the system’s instructions or implementation | An edit can help, hurt, or do nothing |
| Solver | The component that performs the task | An agent choosing ML experiments |
| Improver | A procedure that proposes and tests changes to a solver or improver | A skill-editing and comparison procedure |
| Structural recursion | A changed improvement procedure governs later improvement work | An inherited check changes the next round |
| Effective recursive improvement | The inherited change improves the improvement process under a stated comparison | Requires more than a better current solver score |
| Acceleration | Increasing progress rate across generations under defined resource accounting | Not established by two wins or an upward sketch |
| Selection set | Cases used to choose candidates | Repeated feedback makes them development data |
| Final evaluation | Evaluation of a frozen retained choice | Public partitions are not secret from this host agent |
| Ablation | A controlled removal or disabling of a component | Compare with and without memory |
| Transfer | Applying a retained method beyond the setting that selected it | Test a bike-research skill on wine classification |
| GRPO | Group Relative Policy Optimization; a model-training approach using relative rewards within rollout groups | A grouped-reward calculation alone is not a full training implementation |

The self-* terms overlap. They are not one universal ladder. A system can organize itself without learning, learn without improving, or modify itself without recursion. Name what changed and the evidence for its effect.

## One experiment

Meet these terms in [theme 00](00_start_here/README.md), then use them in [controlled comparisons](02_loop_engineering/README.md).

| Term | Plain meaning | Concrete example and limit |
|---|---|---|
| Prediction unit | What one prediction describes | One hour of bike demand, not one customer or one day. |
| Feature | An input allowed by the prediction contract | Hour of day. A dataset column is not automatically an allowed input. |
| Target / label | The outcome to estimate | Rentals per hour, or whether wine quality is at least 7. |
| Regression | Predict a numerical quantity | Estimate 120 rentals. Regression need not use a linear model. |
| Classification | Predict a category | High-quality wine or not, under a declared threshold. |
| Training | Fit model parameters using training examples | Fit the bike regressor on the designated training rows. |
| Parameter | A value fitted from data | A coefficient in a linear model. |
| Hyperparameter | A model setting chosen outside its fitting step | A tree-depth limit. Changing it does not itself revise the search procedure. |
| Recipe | Declared choices for fitting a candidate | Model family, feature group and seed under a fixed task contract. It is not yet a fitted model. |
| Candidate | A proposed solution or procedure being considered | A model, a skill or an improver. Always say which kind. |
| Exploratory data analysis (EDA) | Inspect data to understand its structure and limits | Examine missing values, duplicates, imbalance and hourly demand before proposing changes. |
| Data card | A readable description of the data and its intended use | Source, permission, version, fields, units, split and known limits. |
| Data provenance | Where data came from and how it changed | The source version and the rule that derives the wine label. |
| Split / partition | Assign examples to different experimental roles | Training fits parameters; selection chooses candidates; final evaluation checks the frozen choice. |
| Training-only preprocessing | Fit transformations without evaluation examples | Learn scaling values from training rows, then apply them to selection rows. |
| Recall | Fraction of actual members of a class that the model finds | Find 6 of 10 actual positive wines: positive recall is 0.6. |
| Class imbalance | Some labels occur much more often than others | High ordinary accuracy can coexist with missing every rare positive. |
| Error slice | A defined subset used to inspect mistakes | MAE at 8 a.m. Better overall MAE need not mean every hour improves. |
| Overfitting | Adapt too closely to observed examples or feedback | A tree fits training data perfectly but predicts other rows poorly. Search can also overfit selection feedback. |
| Seed | A setting that initializes a pseudorandom process | Seed 17 helps repeat a declared recipe. It does not guarantee identical results on all software and hardware. |

**Work through two numbers.** Absolute errors of 10 and 20 rentals give MAE 15 rentals. Class recalls of 0.9 and 0.5 give balanced accuracy 0.7. These metrics answer different questions; do not average them into one course score.

**Change the prediction question.** At noon, you know the observed weather. Yesterday, you did not know today's observed weather. The same column can be permitted for one question and unavailable for another. See [input availability](04_ontology_engineering/step_05_evolve_vocabulary/README.md).

## Working with an agent

Use these terms in the [fixed-process](01_process_without_loops/README.md), [graph](03_graph_engineering/README.md) and [builder](06_meta_harness_engineering/README.md) labs.

| Term | Plain meaning | Concrete example and limit |
|---|---|---|
| Host large language model (LLM) | The language model supplying the agent's text and decisions | A skill edit changes its input instructions, not its pretrained weights. |
| Prompt | Instructions or context for an interaction | “Inspect hourly errors before choosing another recipe.” It may be used once or saved in a skill. |
| Task contract | Rules defining an experiment and its valid comparisons | Target, permitted inputs, metric, partitions and limits. Do not change them to rescue a losing result. |
| Artifact | A saved object used or produced by the work | A brief, prediction file or report. Existence does not establish validity. |
| Workspace | Where an experiment's files and state live | Its ledger and final lock survive a move to the next lesson. |
| State | Current facts needed to select the next action | Active candidate, spent attempts and pending check. |
| Context | Information currently available to the agent | Messages and retrieved files. Different folders do not erase shared context. |
| Memory | Retained information intended for later use | A scoped lesson from a failure. Saving, using and benefiting from it are different claims. |
| Trace / trajectory | A record of actions and observations | Which procedure was read, which tool ran and which decision followed. A later summary is not a contemporaneous trace. |
| Ledger | A persistent account of attempts and resources | Keep failed and interrupted work, not only the winner. |
| Checkpoint | Saved state used to continue work | A workflow checkpoint may preserve a ledger without supporting model-training resumption. |
| Hash / checksum | A digest used to compare file contents | Matching SHA-256 values support byte identity. They do not prove truth, authorship or obedience. |
| Budget | A declared resource allowance | Three attempts across all sessions. Creating another folder does not authorize three more. |
| Branch / router | Choose a route from a condition | Invalid inputs stop; known valid inputs proceed. Unknown is not a pass. |
| Join | Bring required branches or evidence together | Check task and candidate identities before combining results. |
| Invariant | A condition that must hold at a specified boundary | Training and selection rows do not overlap. State where the check runs. |
| Procedural graph | A graph of actions and transitions | Route an invalid handoff to repair. It organizes execution rather than describing domain facts alone. |

**Keep syntax and meaning separate.** A schema can accept the number `0.8` without knowing whether it means accuracy, seconds or MAE. An execution graph can send that record to the correct place. Domain rules still need to check its meaning. Revisit [the three views](03_graph_engineering/step_06_three_views/README.md) and [domain invariants](04_ontology_engineering/step_03_invariants/README.md).

## Following a change

Use [measurement](08_measuring_improvement/README.md) before [the recursive experiment](09_recursive_self_improvement/README.md).

| Term | Plain meaning | Evidence or counterexample |
|---|---|---|
| Recursive self-improvement (RSI) | In this course, an improvement procedure changes and its revision governs later improvement work | Establish the structure first; measure effectiveness separately. Other sources can use different definitions. |
| Meta-skill | A skill that operates on skills or their improvement | A procedure for diagnosing and checking task-skill edits. The prefix does not prove recursion. |
| Mutable surface | What the candidate is allowed to change | A skill, tool or improver rule. The entire filesystem is not automatically in scope. |
| Parent / child | A starting version and a proposed descendant | A rejected child does not automatically become the next active parent. |
| Lineage / generation | Recorded ancestry and an identified round of descendant creation | Generation numbers alone do not say whether the solver or improver changed. |
| Promotion | Accept a candidate as the retained active version | Apply the predeclared rule and keep the supporting checks. |
| Rollback | Restore a previously retained version | Keep the rejected change and its costs. |
| Inheritance | Later work uses a retained procedure or state | A changed rule must cause a later action. Copying the file is insufficient. |
| Persistent learning | Adaptation survives into later work | The later task actually reads and applies the memory or changed procedure. Benefit remains a separate question. |
| Co-evolution | Coupled components change over successive cycles | Model and harness versions interact; this does not imply every updater also improves. |
| Autonomy | How far specified decisions and actions proceed without human intervention | An autonomous process can stay fixed. An author-guided recursive demonstration need not be autonomous. |
| Held-out data | Data excluded from a specified fitting or selection operation | It need not be secret from an agent with file access. |
| Matched comparison | Keep relevant starts and resource allowances comparable | Same initial skill and fit allowance. Equal fits do not imply equal inference costs. |
| Confound | A difference that offers an alternative explanation | The new procedure also receives ten times the attempts. |
| Interaction | A component's effect depends on another component | A memory note helps one skill but conflicts with its child. |
| Negative transfer | A retained adaptation harms another case or task | A bike-specific metric instruction misdirects the wine experiment. |
| Uncertainty | What the evidence leaves unresolved | Three seeds on one split do not measure variation across cities. |
| Counterexample / falsifying case | A case that challenges a rule; a falsifying case is specified to count against a hypothesis | A new check rejects valid outputs as well as invalid ones. |
| Replay | Use already recorded outcomes under another query or policy | A discovery-tree replay cannot reveal a score for an unvisited branch. |
| Simulation | Execute rules over a constructed world | Queue ticks are synthetic units, not measured platform seconds. |
| Mechanism exercise | Execute a small analogue to expose one idea | A laptop grouped-reward calculation does not reproduce LLM training. |
| Reproduction / repeatability | Repeat a declared method and compare evidence | State which code, data, environment and context were reused. Terminology varies across fields. |
| Independent replication | Independently controlled work examines a result | Another local process operated by the same author is not automatically independent. |
| Evidence boundary | Conditions limiting what an observation establishes | Role names do not create isolated contexts or a private evaluator. |

**Percentage points are not relative percent.** Moving from 40% to 60% is a gain of 20 percentage points and a 50% relative increase. Neither number states the attempt budget or test protocol. Put those details beside the result.

## Research and compute

These definitions support the [research studio](10_research_studio/README.md) and [compute guide](compute/README.md). Use the source-linked labs for each paper's exact protocol.

| Term | Plain meaning | Example and limit |
|---|---|---|
| Hypothesis | A testable expectation with a possible failure condition | Adding permitted weather inputs helps a fixed linear recipe on the declared period. |
| Screening | Use a cheaper test to allocate later work | A small-data ranking can change under fuller evaluation. |
| Discovery tree | A branching history of attempted solutions | Measured nodes have executed outcomes; unvisited branches stay unknown. |
| Inner / outer loop | Optimization at two named levels | Search model recipes inside a process that revises the researcher. Nesting alone does not establish effective RSI. |
| Ignition | In the AIDE² discussion, whether better researchers also become better at improving researchers | This needs a separate role comparison; an inner-task win cannot answer it. |
| Policy | A rule or distribution for selecting actions | A game table chooses a move; a research policy chooses an experiment. State which one changes. |
| Rollout | One sampled attempt or action sequence | A game episode or tool-use trajectory. A correct final answer does not prove that the intermediate actions occurred. |
| Reward | A signal used to score an attempt for learning | A game win supplies positive return. A mistaken reward can reinforce the wrong behavior. |
| Advantage | How an action or attempt compares with a baseline | The toy grouped calculation centers rewards at their mean; implementations differ. |
| On-policy | Learning from behavior generated by the policy being improved | Inspect policy versions and collection rules. An expert transcript is not automatically on-policy. |
| GPU | Graphics processing unit, used for suitable parallel computation | More GPU capacity does not repair an invalid experiment. |
| Backend / cluster | The runtime location; a cluster coordinates compute machines | A generated launch file is not proof of execution, cancellation or resume. |
| Checkpoint resumption | Continue supported computation from saved internal state | Restarting a non-resumable fit is a new attempt, not resumed training. |
| Compute budget | Declared limits on computational resources | Fits, tokens, wall time and GPU-hours differ. Unknown costs are not zero. |
| GWAS | Genome-wide association study | Tests associations between genetic variants and a trait. Association alone is not a causal or clinical conclusion. |

## Distinctions that matter

| Easily confused pair | Ask this question | Revisit |
|---|---|---|
| Task model / host language model | Which parameters, if any, were trained? | [System composition](05_system_intelligence/step_01_combine_components/README.md) |
| Skill / tool | Is this an instruction to follow or an operation that executes? | [Make a skill](01_process_without_loops/step_03_make_a_skill/README.md) |
| Harness / meta-harness | Which object runs the task, and which generates that object? | [Generate a harness](06_meta_harness_engineering/step_02_generate/README.md) |
| Schema / ontology / procedure graph | Are we checking form, meaning or the next action? | [Domain entities](04_ontology_engineering/step_01_entities/README.md) |
| Correction / retained learning | Does the change survive and affect another task? | [Retain a lesson](07_understanding_self_star/step_03_persistent_learning/README.md) |
| Modification / improvement | Was the changed version tested and found better? | [Inspect a modification](07_understanding_self_star/step_08_modification/README.md) |
| Organization / emergence / benefit | What arrangement changed, what pattern appeared, and which objective improved? | [Observe a pattern](07_understanding_self_star/step_06_emergence/README.md) |
| Repeated improvement / recursion | Did the procedure producing improvements change and govern later work? | [Three objects](09_recursive_self_improvement/step_01_three_objects/README.md) |
| Structure / effectiveness / acceleration | Did the rule get used, did it help, or did progress rate increase? | [Audit the claim](09_recursive_self_improvement/step_07_claim/README.md) |
| Fresh process / fresh agent context | Which prior information can the agent still access? | [Frozen memory](10_research_studio/01_memory_and_exploration/step_05_frozen_memory/README.md) |

Avoid “self-emerging” without an explanation. Name the collective pattern, its proposed interaction mechanism and the intervention that tests it. A label should not replace an account of what happened.

Ask the tutor:

```text
Explain this term using my current experiment.
Show one example and one counterexample.
Name the artifact that would demonstrate it.
Then ask me to explain a new case.
```

For quick practice, classify: a corrected report with no retained rule; a saved rule used tomorrow; a revised updater used to choose tomorrow's rule. Identify the changed object before deciding whether any case improved.

<details>
<summary>Compare your explanation</summary>

The first is local correction. The second shows retained state and, if its trace supports it, later use. The third can show structural recursion when the revised updater actually governs later improvement work. None of those descriptions alone establishes benefit under a fair comparison.

</details>
