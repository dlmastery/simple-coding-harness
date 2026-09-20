# A visual guide to the course

[Course](README.md) · [Start here](START-HERE.md)

Use these illustrations to preview an idea or revisit a distinction. Follow the [learning path](LEARNING-PATH.md) for the actual lesson order; this gallery does not replace the experiments, checks, or quizzes. Each figure links to the lab that explains its mechanism. Open dense figures at full size when reading on a phone.

These are conceptual illustrations. Measured results appear as separate plots with their data and execution records.

## From one experiment to RSI

![Three objects can change: a task model, a research skill, and the improver that revises skills. A proposed improver is checked, accepted or rejected, and an accepted version governs a later round under fixed evaluation.](assets/illustrations/main-overview-v2.png)

*This is a conceptual path, not a measured success story. The last panel shows what an accepted revision would require: the later round reads I1 and uses its added counterexample check. Saving I1 alone is insufficient. Whether it helps requires a fair comparison; rejection remains a valid result.*

[Open the illustration at full size](assets/illustrations/main-overview-v2.png).

[Lab 09.01: Identify the solver, improver, and evaluator](09_recursive_self_improvement/step_01_three_objects/README.md).

## The answer hidden in an input

![Calendar and observed weather enter the model. Casual and registered counts add to total rentals, so their shortcut into features is blocked. Prediction and observation meet at the error check.](assets/illustrations/target-leakage-v2.png)

*The component counts already reveal the answer: casual + registered = total rentals. Keep them out of the input features. The checker still needs the observed total to measure error. This course uses observed weather for a retrospective teaching task; it does not assume that weather was known a day ahead.*

[Open the illustration at full size](assets/illustrations/target-leakage-v2.png).

[Lab 00.01: Meet the prediction task](00_start_here/step_01_meet_the_task/README.md).

## A loop needs memory and a way out

![Propose, run, check, and record surround persistent state. A limit gate leads to the next attempt or stop. A failed fit is recorded and still consumes an attempt. Resumption reads the same saved state.](assets/illustrations/bounded-loop-v1.png)

*The notebook survives the process. Read the remaining budget before another attempt, reserve that attempt before fitting, and preserve failures. A successful fit still needs checking. After interruption, reconcile any in-progress attempt before deciding what can run next; do not reset the allowance.*

[Open the illustration at full size](assets/illustrations/bounded-loop-v1.png).

[Lab 02.02: Give the loop state and a budget](02_loop_engineering/step_02_bounded_state/README.md).

## Workflow and domain meaning

![A workflow graph routes valid data toward fitting and invalid data toward repair. Separate domain relations say the scaler is fit on training data, search selects on selection data, and the model is measured by MAE.](assets/illustrations/graph-ontology-v1.png)

*Read the left arrows as dependencies between actions. Read the right arrows as sentences about domain meaning. These are selected facts and one rule, not a complete ontology. Correct execution order cannot rescue a leaked feature or the wrong metric. A declared fact also needs evidence that the implementation follows it.*

[Open the illustration at full size](assets/illustrations/graph-ontology-v1.png).

[Lab 04.02: Connect data, models, and evidence](04_ontology_engineering/step_02_relations/README.md).

## The builder and the system it builds

![A task brief enters an unchanged meta-harness builder. It produces a separate package of skills, tools, state, checks, and limits. The package then runs a model and produces predictions and a checked report.](assets/illustrations/meta-harness-v2.png)

*In this example the builder stays fixed. It creates a package that must then run under the brief’s limits. Files alone do not show that the package works. A checked execution provides evidence about the generated harness; it does not establish that the builder improved itself.*

[Open the illustration at full size](assets/illustrations/meta-harness-v2.png).

[Lab 06.02: Generate a first harness](06_meta_harness_engineering/step_02_generate/README.md).

## Similar words, different changes

![Eight parallel examples show current-output correction, tested reflection, retained learning, task-skill improvement under a fixed improver, local reorganization, emergence, self-play under a fixed update rule, and active instruction modification.](assets/illustrations/self-star-v2.png)

*These are examples of mechanisms, not mutually exclusive categories or a maturity ladder. A system can combine them. The self-play panel changes policy values under a fixed update rule; the modification panel changes active instructions without proving a benefit. The emergence drawing is a conceptual group-pattern analogy, not a measurement from the queue exercise. Ask what changed, what persisted, and how its effect was checked.*

[Open the illustration at full size](assets/illustrations/self-star-v2.png).

[Lab 07.08: Make a self-modification inspectable](07_understanding_self_star/step_08_modification/README.md).

## The next round must use the change

![A proposed improver adds a contrasting-case check. Acceptance activates that same version in a later round, where the new check is executed. Rejection keeps I0 active. A later task-skill proposal can also be rejected.](assets/illustrations/inherited-improver-v1.png)

*The highlighted instruction appears in proposed I1, active I1, and the later executed check. That connection matters more than a new filename. The image shows a possible accepted path; the course’s two-generation comparison rejected both improver proposals. An inherited change can also perform worse. Keep version identity, observed use, and measured benefit as separate claims.*

[Open the illustration at full size](assets/illustrations/inherited-improver-v1.png).

[Lab 09.04: Use the revised improver in the next round](09_recursive_self_improvement/step_04_inherit/README.md).

## Replay stops at the edge of the record

![Replay follows a recorded baseline and tried change, while a failed attempt remains archived. It stops before an untried branch whose outcome is unknown. A separate new execution would produce a new report.](assets/illustrations/replay-boundary-v2.png)

*The left panel is the record before another run. Replay can reuse its supported outcomes and failure status; it cannot supply D’s missing result. The right panel shows the additional execution needed to extend that record. This is a classroom mechanism inspired by Dream-RSI, not a reproduction of its benchmark or a claim that all counterfactual policies are covered.*

[Open the illustration at full size](assets/illustrations/replay-boundary-v2.png).

[Lab 10.08: Replay only what the history can answer](10_research_studio/02_dream_rsi/step_08_replay/README.md).

## Track the model and harness together

![Versioned pairs progress from H0 with M0 to H1 with M0, then H1 with M1. The first change edits harness instructions; the second updates model parameters. Training evidence goes to the update, while held-out cases remain in external evaluation.](assets/illustrations/model-harness-v2.png)

*Track both versions because a harness and model can interact. First hold M0 fixed while changing the harness; then hold H1 fixed while changing weights. Keep training evidence separate from the cases used for the declared external comparison, and do not feed final results back into selection. This lab illustrates pair accounting with synthetic scores. It does not train an LLM or reproduce ScienceBuddy’s reported gains.*

[Open the illustration at full size](assets/illustrations/model-harness-v2.png).

[Lab 10.25: Track model–harness pairs across cycles](10_research_studio/07_sciencebuddy/step_25_coevolution/README.md).

## Move the compute, preserve the evidence

![A research skill passes a versioned experiment contract to an adapter that can select local CPU, accelerator, or cluster execution. Every backend returns an identified attempt record with status and total cost.](assets/illustrations/compute-contract-v2.png)

*The backends are alternatives. Preserve the scientific contract when moving the same experiment; declare a new one when changing the task, data, or comparison. A candidate can have several submission attempts, so record both identities and all failures. Checkpoint resumption applies only when the job supports it. The course tests the local CPU path; accelerator and cluster adapters still need tests on the actual systems.*

[Open the illustration at full size](assets/illustrations/compute-contract-v2.png).

[The larger-compute guide](compute/README.md).
