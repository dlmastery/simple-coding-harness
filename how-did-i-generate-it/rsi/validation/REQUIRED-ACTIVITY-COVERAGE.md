# Required activity coverage

This inventory separates authored instructions from execution evidence. It covers all 101 lab READMEs at the current source revision. The [editorial inventory](README-GUIDANCE-COVERAGE.md) answers a different question.

101 labs have mapped related author-execution evidence; 0 do not yet have a lab-specific execution mapping here. **These are mapping counts, not completed-lab counts.** Unmapped means unverified in this inventory, not proof that a mechanism has never run. Component tests, primary-source reading, and a progress-file assertion do not automatically satisfy a lesson activity.

Each entry retains the required steps, the additional change, the closest known execution record, and a closure gap. To close an activity, name its actual input, command or action, output, check, and budget in the execution record. Preserve failed attempts. Source-review activities need the specific inspected primary sections and a completed claim audit; an abstract link alone is insufficient.

All learner predictions, quizzes, and teach-back remain unattempted by a real student unless later evidence explicitly says otherwise. Other native-agent contexts and optional GPU/cluster backends remain separate checks. No lab is declared fully validated by this generated inventory.

The selected journey's [scope and omissions](CLEAN-JOURNEY-RESULTS.md) govern its evidence. Later runs must use new, declared experiments; never reopen a final-locked workspace to fill a coverage gap.

## 00 · Start with a prediction

### [00.01 · Meet the prediction task](../../../rsi/00_start_here/step_01_meet_the_task/README.md)

1. **Inspect one hour.** Start with a row you can understand.
2. **Write the brief.** Make the prediction setting explicit.

**Additional change:** Change the request to “predict tomorrow at noon.” Before training anything, list which inputs would now be unknown. Save the changed brief as a separate task.

**Evidence:** [Selected author execution](../../../rsi/evidence/2026-09-20/clean-journey/00-01).

**Closure gap:** Reconcile each action and the additional change below with its files. A directory or progress note alone does not close the lab.

**Acceptance to verify:** TASK.md excludes casual and registered from prediction inputs. It states rentals per hour as the target unit and distinguishes observed weather from a forecast.

### [00.02 · Prepare a workspace you can inspect](../../../rsi/00_start_here/step_02_prepare_the_workspace/README.md)

1. **Check capabilities.** Find the actual execution path.
2. **Inspect the data.** Confirm that the supplied source is intact.

**Additional change:** Ask the agent what it could still do if command execution were disabled. Separate explanation from completion of the experiment.

**Evidence:** [Selected author execution](../../../rsi/evidence/2026-09-20/clean-journey/00-02).

**Closure gap:** Reconcile each action and the additional change below with its files. A directory or progress note alone does not close the lab.

**Acceptance to verify:** CAPABILITIES.md identifies the runtime. DATA-REPORT.md and a readable chart exist. Source checksum verification passes. The report states that public partitions are not secret.

### [00.03 · Run one baseline](../../../rsi/00_start_here/step_03_one_attempt/README.md)

1. **Run the fixed recipe.** Create an actual baseline.
2. **Check three errors.** Connect the score to individual predictions.

**Additional change:** Without another fit, compare an error at a quiet hour with one at a busy hour. Explain why a single prediction can be wrong in different directions.

**Evidence:** [Selected author execution](../../../rsi/evidence/2026-09-20/clean-journey/00-03).

**Closure gap:** Reconcile each action and the additional change below with its files. A directory or progress note alone does not close the lab.

**Acceptance to verify:** There is exactly one successful trial. The prediction is constant. The reported full MAE matches a recomputation over saved predictions. No final evaluation has run.

### [00.04 · Check the evidence behind the answer](../../../rsi/00_start_here/step_04_check_the_evidence/README.md)

1. **Trace the result.** Follow evidence from claim to rows.
2. **Catch a false summary.** Test the check with a deliberate mistake.

**Additional change:** Imagine the metric matches but the predictions came from training rows. Explain why an arithmetic check would pass while the scientific claim fails.

**Evidence:** [Selected author execution](../../../rsi/evidence/2026-09-20/clean-journey/00-04).

**Closure gap:** Reconcile each action and the additional change below with its files. A directory or progress note alone does not close the lab.

**Acceptance to verify:** EVIDENCE.md links the actual files. The correct report passes and the altered summary fails. The report does not claim an independent evaluator or RSI.

## 01 · Make one process dependable

### [01.01 · Write the data science process](../../../rsi/01_process_without_loops/step_01_describe_the_process/README.md)

1. **Name the actions.** Turn intentions into observable work.
2. **Walk one record through.** Check that the sequence has no unexplained jump.

**Additional change:** Move split design after fitting. Explain what temptation this creates and why a later good score would be harder to interpret.

**Evidence:** [Selected author execution](../../../rsi/evidence/2026-09-20/clean-journey/01-01).

**Closure gap:** Reconcile each action and the additional change below with its files. A directory or progress note alone does not close the lab.

**Acceptance to verify:** Each action has a concrete input and output. Task, split, and metric are fixed before model fitting. The process contains no learner-designed improvement loop.

### [01.02 · Run the process without changing it](../../../rsi/01_process_without_loops/step_02_run_the_process/README.md)

1. **Execute the sequence.** Test whether the written process is sufficient.
2. **Compare the runs.** Separate reproducibility from performance improvement.

**Additional change:** Remove an output report from a copy of the new workspace. Have the agent distinguish a missing artifact from an unexecuted model fit.

**Evidence:** [Selected author execution](../../../rsi/evidence/2026-09-20/clean-journey/01-02).

**Closure gap:** Reconcile each action and the additional change below with its files. A directory or progress note alone does not close the lab.

**Acceptance to verify:** The trace contains all five actions. The score recomputes from the new predictions. Any version difference is visible.

### [01.03 · Turn the process into a skill](../../../rsi/01_process_without_loops/step_03_make_a_skill/README.md)

1. **Write a focused skill.** Preserve the process outside chat.
2. **Read and follow it.** Check that its instructions govern execution.

**Additional change:** Add an ambiguous instruction, “use the best data.” Identify two conflicting interpretations, then replace it with a concrete input-availability rule.

**Evidence:** [Selected author execution](../../../rsi/evidence/2026-09-20/clean-journey/01-03).

**Closure gap:** Reconcile each action and the additional change below with its files. A directory or progress note alone does not close the lab.

**Acceptance to verify:** The skill names its stop condition and reports. An actual execution follows it. A prose restriction is not described as a sandbox.

### [01.04 · Check outputs with a separate calculation](../../../rsi/01_process_without_loops/step_04_separate_the_check/README.md)

1. **Generate the checker.** Give the check its own inputs.
2. **Substitute one row.** Demonstrate an actual refusal.

**Additional change:** Give the checker only a metric number without predictions. Explain which checks become impossible.

**Evidence:** [Generated separate checker with actual pass and row-substitution refusal](../../../rsi/evidence/2026-09-22/generated-checker/README.md).

**Closure gap:** The generated standard-library implementation checks the archived baseline, then refuses one changed source-row ID in exactly two invocations and zero fits. One-cell differences and five source identities are retained; the metric-only limitation is explained. This closes the prior supplied-checker reuse gap. Same author context, trusted references, untested other tampering branches and unattempted learner responses limit the result.

**Acceptance to verify:** The valid file passes and the substituted-row file fails. CHECK-REPORT.md describes exactly what the checker reads and cannot protect.

### [01.05 · Reuse the skill in a fresh session](../../../rsi/01_process_without_loops/step_05_reuse_the_skill/README.md)

1. **Prepare the handoff.** Retain only the necessary starting information.
2. **Run from files.** Test the real context boundary available.

**Additional change:** Remove the task brief from a handoff copy. Have the new session identify the missing scientific choices instead of guessing a flattering metric.

**Evidence:** [Selected author execution](../../../rsi/evidence/2026-09-20/clean-journey/01-05).

**Closure gap:** Same author context; the requested fresh-agent handoff is untested. A new process is not a new coding-agent context.

**Acceptance to verify:** The handoff identifies every required artifact. The new run is real. The report distinguishes fixed reuse from adaptive improvement.

## 02 · Repeat for a reason

### [02.01 · Let a failure motivate a second attempt](../../../rsi/02_loop_engineering/step_01_why_repeat/README.md)

1. **Inspect the failure pattern.** Choose a change for a reason.
2. **Run the comparison.** Measure a controlled change.

**Additional change:** Inspect a slice where the new model is still weak. Explain why a better average does not imply every hour improved.

**Evidence:** [Selected author execution](../../../rsi/evidence/2026-09-20/clean-journey/02-01).

**Closure gap:** Reconcile each action and the additional change below with its files. A directory or progress note alone does not close the lab.

**Acceptance to verify:** The data, split, metric, seed, and feature set match. Only the model family changes. COMPARISON.md retains both results and costs.

### [02.02 · Give the loop state and a budget](../../../rsi/02_loop_engineering/step_02_bounded_state/README.md)

1. **Declare the state.** Make the next action inspectable.
2. **Execute three steps.** Follow the declared loop.

**Additional change:** Set the limit to one in a new workspace. Predict which artifact can be produced and which comparisons cannot.

**Evidence:** [Selected author execution](../../../rsi/evidence/2026-09-20/clean-journey/02-02).

**Closure gap:** Reconcile each action and the additional change below with its files. A directory or progress note alone does not close the lab.

**Acceptance to verify:** Exactly three attempts are recorded. The retained candidate satisfies the declared rule. The last candidate is not automatically selected.

### [02.03 · Turn an error into a different action](../../../rsi/02_loop_engineering/step_03_use_feedback/README.md)

1. **Write a diagnosis.** Turn observations into a falsifiable proposal.
2. **Use the feedback.** Record the decision it changed.

**Additional change:** Replace the diagnosis with “try harder.” Explain why this is less useful than naming a testable change.

**Evidence:** [Selected author execution](../../../rsi/evidence/2026-09-20/clean-journey/02-03).

**Closure gap:** Reconcile each action and the additional change below with its files. A directory or progress note alone does not close the lab.

**Acceptance to verify:** The next action differs in the declared feature set. The report does not infer causation from prediction performance. Harmful feedback remains visible.

### [02.04 · Stop repeated failure and oscillation](../../../rsi/02_loop_engineering/step_04_stop_the_loop/README.md)

1. **Build the stop check.** Give repetition an observable definition.
2. **Test the limit.** Verify behavior, including rejection.

**Additional change:** Label a repeated seed experiment as an intentional reproducibility check. Explain why its purpose and cost should remain explicit.

**Evidence:** [Selected author execution](../../../rsi/evidence/2026-09-20/clean-journey/02-04).

**Closure gap:** Reconcile each action and the additional change below with its files. A directory or progress note alone does not close the lab.

**Acceptance to verify:** The controller produces a real refusal for both duplicate and over-budget requests. Rejections are recorded without fabricated model scores.

### [02.05 · Resume without losing the experiment](../../../rsi/02_loop_engineering/step_05_resume/README.md)

1. **Stop at a boundary.** Save a state you can inspect.
2. **Resume from files.** Continue the same experiment.

**Additional change:** Prepare a labelled teaching checkpoint with a running trial whose process has exited. Mark it interrupted and preserve its spent attempt before continuing.

**Evidence:** [Selected author execution](../../../rsi/evidence/2026-09-20/clean-journey/02-05).

**Closure gap:** A clean stop between commands was resumed. Forced process interruption and stale-lock recovery were not exercised.

**Acceptance to verify:** Candidate IDs are unique. The first result survives. The restart does not replenish attempts. A stale lock is inspected before removal.

### [02.06 · Compare two ways to spend the same attempts](../../../rsi/02_loop_engineering/step_06_compare_loops/README.md)

1. **Declare the comparison.** Prevent a favorable retrospective choice.
2. **Run and interpret.** Measure retained outputs and costs.

**Additional change:** Give one arm ten attempts only as a clearly separate exercise. Explain why its better result would not establish a better method at equal resources.

**Evidence:** [Executed loop, routing, context, ablation, and repetition activities](../../../rsi/evidence/2026-09-20/loops-and-systems/README.md).

**Closure gap:** Four matched-budget fits and a pre-fit adaptive choice executed. The unequal-budget extension was explained but its additional fits were not run. Baseline outcomes were author-known; inference cost is unmeasured.

**Acceptance to verify:** Both arms start from the same recipe and get two fits. The adaptive choice is recorded before evaluation. The conclusion is limited to this small comparison.

## 03 · Give different cases different routes

### [03.01 · Draw the dependencies](../../../rsi/03_graph_engineering/step_01_dependencies/README.md)

1. **Name the dependencies.** Explain order through required inputs.
2. **Validate an ordering.** Turn the graph into a small executable check.

**Additional change:** Remove the inspect-to-split edge in a copy. Explain what important information the split designer could now miss.

**Evidence:** [Selected author execution](../../../rsi/evidence/2026-09-20/clean-journey/03-01).

**Closure gap:** Reconcile each action and the additional change below with its files. A directory or progress note alone does not close the lab.

**Acceptance to verify:** The graph has explicit edges and a valid order. The checker rejects the invalid order. The diagram labels artifacts rather than implying unexplained communication.

### [03.02 · Route different failures differently](../../../rsi/03_graph_engineering/step_02_branch/README.md)

1. **Define the branch.** Make each route meaningful.
2. **Run all routes.** Test the conditions instead of only the happy path.

**Additional change:** Change “unknown means stop” to “unknown means pass” in a labelled copy. Show which faulty input is now accepted.

**Evidence:** [Selected author execution](../../../rsi/evidence/2026-09-20/clean-journey/03-02).

**Closure gap:** Reconcile each action and the additional change below with its files. A directory or progress note alone does not close the lab.

**Acceptance to verify:** All three states are exercised. No invalid or unknown input reaches the fit action. Fixture mutations stay outside source data.

### [03.03 · Join independent checks](../../../rsi/03_graph_engineering/step_03_join/README.md)

1. **Define the join.** State what must agree.
2. **Exercise mismatches.** Test missing and stale results.

**Additional change:** Delay one check result in a local simulation. Explain why the other result alone cannot authorize the next action.

**Evidence:** [Executed foundation cases and additional changes](../../../rsi/evidence/2026-09-21/foundation-gaps/README.md).

**Closure gap:** Four joins now execute, including wrong contract and the late-result simulation within the missing case. Resource inputs are declared fixtures; actual concurrent workers, machine capacity, and learner responses were not tested.

**Acceptance to verify:** The join rejects mismatched candidate identities, mismatched contract versions, and incomplete evidence. The report states whether checks ran sequentially or concurrently.

### [03.04 · Put a bounded retry inside the graph](../../../rsi/03_graph_engineering/step_04_cycle/README.md)

1. **Add the cycle.** Preserve state across the return edge.
2. **Test success and exhaustion.** Check both exit paths.

**Additional change:** Remove the failure feedback from the repair input. Predict how that could waste attempts even with a valid stop rule.

**Evidence:** [Selected author execution](../../../rsi/evidence/2026-09-20/clean-journey/03-04).

**Closure gap:** Reconcile each action and the additional change below with its files. A directory or progress note alone does not close the lab.

**Acceptance to verify:** Both traces end. Attempts are monotonic and bounded. The verifier rule is unchanged between checks.

### [03.05 · Resume only the affected work](../../../rsi/03_graph_engineering/step_05_recover/README.md)

1. **Inject a reporting failure.** Keep upstream computation valid.
2. **Recover selectively.** Use dependencies to decide what to reuse.

**Additional change:** Try reusing a metric report after substituting a prediction file. Require the version check to detect the stale dependency.

**Evidence:** [Selected author execution](../../../rsi/evidence/2026-09-20/clean-journey/03-05).

**Closure gap:** Reconcile each action and the additional change below with its files. A directory or progress note alone does not close the lab.

**Acceptance to verify:** The successful recovery does not create an extra fit. The changed-split case invalidates all dependent evidence.

### [03.06 · Read the plan, data flow, and trace](../../../rsi/03_graph_engineering/step_06_three_views/README.md)

1. **Separate the views.** Make their questions distinct.
2. **Find the mismatch.** Use a failed run to test the distinction.

**Additional change:** Add a new check node to the plan without rerunning the experiment. Explain why old results do not gain that check retroactively.

**Evidence:** [Rendered views and audit of existing run records](../../../rsi/evidence/2026-09-21/three-views/README.md).

**Closure gap:** Three separate diagrams, artifact table, failure audit, and unexecuted plan extension are retained. Recovery chronology is reconstructed from program order and retained outputs; exact event timestamps and a separate recovery journal are absent. Learner interpretation was not tested.

**Acceptance to verify:** VIEWS.md distinguishes permission to act, required data, and observed execution. Every claimed completed check has a trace event and output.

## 04 · Agree on what the experiment means

### [04.01 · Name the objects in an experiment](../../../rsi/04_ontology_engineering/step_01_entities/README.md)

1. **Build the vocabulary.** Ground each term in an actual artifact.
2. **Classify a confusing case.** Test whether definitions help.

**Additional change:** Replace every use of “score” with its precise metric, candidate, partition, and unit. Notice which missing context becomes visible.

**Evidence:** [Selected author execution](../../../rsi/evidence/2026-09-20/clean-journey/04-01).

**Closure gap:** Reconcile each action and the additional change below with its files. A directory or progress note alone does not close the lab.

**Acceptance to verify:** Definitions include concrete examples and do not equate a recipe with a fitted model or a metric with its measured value.

### [04.02 · Connect data, models, and evidence](../../../rsi/04_ontology_engineering/step_02_relations/README.md)

1. **Write the facts.** Turn relationships into complete sentences.
2. **Check the declared relations.** Run the small supplied semantic checker.

**Additional change:** Draw the execution graph beside the relation table. Identify one node name that appears in both but has a different role.

**Evidence:** [Selected author execution](../../../rsi/evidence/2026-09-20/clean-journey/04-02).

**Closure gap:** Reconcile each action and the additional change below with its files. A directory or progress note alone does not close the lab.

**Acceptance to verify:** Each relation is understandable as a sentence. The checker runs and the report states its limited coverage.

### [04.03 · State rules that must always hold](../../../rsi/04_ontology_engineering/step_03_invariants/README.md)

1. **Pair rules with examples.** Make each rule testable.
2. **Execute the examples.** Verify the rules have consequences.

**Additional change:** Add a new rule that MAE measurements must include units. Ask the agent to implement it in a workspace extension and run one case with units and one without. Keep this two-case extension separate from the six base cases; the original tool does not check units.

**Evidence:** [Executed foundation cases and additional changes](../../../rsi/evidence/2026-09-21/foundation-gaps/README.md).

**Closure gap:** Six base cases and two separate units-extension cases now execute with individual inputs and verdicts. Units checks require a label only. Unknown-relation rejection was source-inspected but not separately executed in this allocation; omitted facts and learner understanding remain untested.

**Acceptance to verify:** Every invariant has a demonstrated negative case. Unknown relations are not silently accepted.

### [04.04 · Catch a plausible but invalid experiment](../../../rsi/04_ontology_engineering/step_04_catch_contradictions/README.md)

1. **Create the contradiction.** Make the error about meaning, not syntax.
2. **Repair the record.** Correct facts without erasing the failure.

**Additional change:** In a separate copy of the failed table, rename total_users to harmless_feature in both related facts. Run the third check and confirm that the derivation relation still triggers rejection.

**Evidence:** [Executed foundation cases and additional changes](../../../rsi/evidence/2026-09-21/foundation-gaps/README.md).

**Closure gap:** Original, corrected, and consistently renamed tables now execute with failure counts three, zero, and three. Record repair does not validate a real leaked experiment; no learner responses were collected.

**Acceptance to verify:** The original table fails with three concrete reasons. The corrected copy passes the supplied rules. The report distinguishes correcting documentation from rerunning invalid computation.

### [04.05 · Change a definition without losing its consequences](../../../rsi/04_ontology_engineering/step_05_evolve_vocabulary/README.md)

1. **Version the definition.** State the changed scientific question.
2. **Trace the impact.** Connect meaning changes to work that must be redone.

**Additional change:** Apply the same reasoning to wine quality: replace the binary threshold with ordinal prediction. Identify which metrics and model choices must be reconsidered.

**Evidence:** [Selected author execution](../../../rsi/evidence/2026-09-20/clean-journey/04-05).

**Closure gap:** Reconcile each action and the additional change below with its files. A directory or progress note alone does not close the lab.

**Acceptance to verify:** IMPACT.md identifies invalid evidence reuse and missing data. The availability rule has a demonstrated rejection. No unrun forecasting score is invented.

## 05 · Build capability around the model

### [05.01 · Combine fixed components into a useful system](../../../rsi/05_system_intelligence/step_01_combine_components/README.md)

1. **Assign responsibilities.** Avoid giving every component an undefined job.
2. **Run the fixed system.** Observe coordinated behavior.

**Additional change:** Remove the domain check in a labelled diagnostic copy. Replace fitting with a dry-run stub and reuse the leaked fixture without another fit. Record which protection is lost and whether another guard still blocks it.

**Evidence:** [Selected author execution](../../../rsi/evidence/2026-09-20/clean-journey/05-01).

**Closure gap:** Reconcile each action and the additional change below with its files. A directory or progress note alone does not close the lab.

**Acceptance to verify:** The valid run passes the intended checks. The invalid fixture does not reach fitting. No component is silently revised during the comparison.

### [05.02 · Choose a skill for the task](../../../rsi/05_system_intelligence/step_02_route_tasks/README.md)

1. **Build the route table.** Connect task meaning to method.
2. **Execute both routes.** Test transfer of the system structure.

**Additional change:** Give the router a task with no target type. Require a clarification of the scientific question before choosing a metric.

**Evidence:** [Executed loop, routing, context, ablation, and repetition activities](../../../rsi/evidence/2026-09-20/loops-and-systems/README.md).

**Closure gap:** Declared fits and fixtures, source identities, additional analysis, and measured outputs are retained. The fixed router and guards are agent-written code in one author context; no real learner assessment or independent language-model behavior is established.

**Acceptance to verify:** The two tasks use their own contracts. Identical wine feature rows stay in one partition. Unknown tasks are rejected.

### [05.03 · Retrieve what matters and retain task state](../../../rsi/05_system_intelligence/step_03_context_and_state/README.md)

1. **Build the packet.** Separate information by role.
2. **Test stale context.** Make a conflict visible.

**Additional change:** Remove the data card’s input-availability rule and ask which next decision becomes unsafe to infer.

**Evidence:** [Executed loop, routing, context, ablation, and repetition activities](../../../rsi/evidence/2026-09-20/loops-and-systems/README.md).

**Closure gap:** Declared fits and fixtures, source identities, additional analysis, and measured outputs are retained. The fixed router and guards are agent-written code in one author context; no real learner assessment or independent language-model behavior is established.

**Acceptance to verify:** The packet preserves current task identity and ledger state. A stale budget note produces a visible conflict.

### [05.04 · Coordinate planning, execution, and checking](../../../rsi/05_system_intelligence/step_04_coordinate/README.md)

1. **Define the handoffs.** Make completion requirements explicit.
2. **Run and interrupt handoffs.** Test more than a successful path.

**Additional change:** Have a tool return a valid score for the wrong candidate. Require the coordinator to reject that handoff.

**Evidence:** [Executed live state control and process resumption](../../../rsi/evidence/2026-09-20/live-coordinator/README.md).

**Closure gap:** One new fit, a later check process, three handoff fixtures, and post-completion refusal executed. The earlier retrospective trace and its separate fit remain preserved. Forced interruption during fitting, independent reviewers, and learner interpretation were not tested.

**Acceptance to verify:** The coordinator never marks incomplete work complete. Its report states that role separation is organizational unless an actual access boundary exists.

### [05.05 · Find which component makes the difference](../../../rsi/05_system_intelligence/step_05_ablate_system/README.md)

1. **Predeclare the outcome.** Avoid choosing the metric after the result.
2. **Run both versions.** Measure the component’s contribution.

**Additional change:** Remove both overlapping checks in a separate declared ablation. Run the same valid and leaked fixtures through the fit stub, for two additional executions and no model fits. Explain why this answers a different causal question.

**Evidence:** [Executed loop, routing, context, ablation, and repetition activities](../../../rsi/evidence/2026-09-20/loops-and-systems/README.md).

**Closure gap:** Declared fits and fixtures, source identities, additional analysis, and measured outputs are retained. The fixed router and guards are agent-written code in one author context; no real learner assessment or independent language-model behavior is established.

**Acceptance to verify:** Only one component differs. The report accounts for redundant checks and does not claim a predictive-performance gain.

## 06 · Generate a harness from a brief

### [06.01 · Describe the harness you need](../../../rsi/06_meta_harness_engineering/step_01_write_a_brief/README.md)

1. **Write the intent.** State scientific and operating rules.
2. **Review ambiguity.** Find missing decisions before generation.

**Additional change:** Remove the metric and ask two plausible alternatives. Explain why choosing one after seeing results would be invalid.

**Evidence:** [Selected author execution](../../../rsi/evidence/2026-09-20/clean-journey/06-01).

**Closure gap:** Reconcile each action and the additional change below with its files. A directory or progress note alone does not close the lab.

**Acceptance to verify:** The brief fixes target, inputs, metric, partitions, resources, and required rejection. It does not require the student to write code or schemas.

### [06.02 · Generate a first harness](../../../rsi/06_meta_harness_engineering/step_02_generate/README.md)

1. **Generate the system.** Let the agent supply implementation syntax.
2. **Run the baseline.** Prove that the generated system executes.

**Additional change:** Ask what would happen if the builder were removed after generation. The generated harness should still have its required task instructions and dependencies.

**Evidence:** [Selected author execution](../../../rsi/evidence/2026-09-20/clean-journey/06-02).

**Closure gap:** Reconcile each action and the additional change below with its files. A directory or progress note alone does not close the lab.

**Acceptance to verify:** The generated system executes its baseline. The result follows the original brief. Missing capabilities are reported, not replaced with simulated success.

### [06.03 · Inspect what the builder decided](../../../rsi/06_meta_harness_engineering/step_03_inspect_generated/README.md)

1. **Map requirements.** Connect intent to actual behavior.
2. **Inspect one hidden assumption.** Find a plausible failure before it scales.

**Additional change:** In a diagnostic copy, alter the README’s budget while leaving code unchanged. Explain why a documentation-only review misses the mismatch.

**Evidence:** [Selected author execution](../../../rsi/evidence/2026-09-20/clean-journey/06-03).

**Closure gap:** Reconcile each action and the additional change below with its files. A directory or progress note alone does not close the lab.

**Acceptance to verify:** The review distinguishes stated, implemented, and executed requirements. Any generated assumption is explicit.

### [06.04 · Test the generated harness’s boundaries](../../../rsi/06_meta_harness_engineering/step_04_test_refusal/README.md)

1. **Run a valid case.** Establish the intended path.
2. **Attempt two violations.** Check request-specific enforcement.

**Additional change:** Remove candidate identity from a check fixture and verify that the system treats it as incomplete evidence.

**Evidence:** [Selected author execution](../../../rsi/evidence/2026-09-20/clean-journey/06-04).

**Closure gap:** Reconcile each action and the additional change below with its files. A directory or progress note alone does not close the lab.

**Acceptance to verify:** Invalid requests do not fit models. An unrelated result cannot satisfy the current candidate’s check. All attempts and refusal costs remain visible.

### [06.05 · Generate a classification harness](../../../rsi/06_meta_harness_engineering/step_05_second_task/README.md)

1. **Describe the new task.** Keep the student interface readable.
2. **Generate and compare.** Test actual adaptation.

**Additional change:** Ask for an ordinal wine task in a new brief without running it. Identify why the binary evaluator cannot be reused unchanged.

**Evidence:** [Selected author execution](../../../rsi/evidence/2026-09-20/clean-journey/06-05).

**Closure gap:** Reconcile each action and the additional change below with its files. A directory or progress note alone does not close the lab.

**Acceptance to verify:** The builder uses the classification contract. Identical feature rows do not cross partitions. The comparison explains shared workflow and changed scientific components.

### [06.06 · Recreate and compare generated harnesses](../../../rsi/06_meta_harness_engineering/step_06_recreate/README.md)

1. **Prepare the clean starts.** Remove dependence on the old chat.
2. **Reproduce and explain.** Compare behavior under the same task contract.

**Additional change:** Change the builder’s proposal instructions and label it a new builder version. State the comparison needed before calling it a better builder.

**Evidence:** [Selected author execution](../../../rsi/evidence/2026-09-20/clean-journey/06-06).

**Closure gap:** Saved generated packages ran in fresh output state. Independent regeneration from the brief in another agent is untested.

**Acceptance to verify:** Both task contracts remain intact. Actual runs and negative checks are recorded. The report does not confuse generator output diversity with improvement.

## 07 · Separate the self-* ideas

### [07.01 · Correct one result](../../../rsi/07_understanding_self_star/step_01_correction/README.md)

1. **Expose the mismatch.** Make correction depend on evidence.
2. **Correct the output.** Change only the current artifact.

**Additional change:** Start a fresh session, where available, with the same fixed procedure and another labelled wrong summary. Inspect and record whether the host also exposes the earlier correction or saved memory. Check the later report without a new model fit and explain why the first correction alone did not guarantee prevention. Label a same-context exercise if a fresh session is unavailable.

**Evidence:** [Executed self-* and measurement activities with labelled replays](../../../rsi/evidence/2026-09-20/self-star-and-measurement/README.md).

**Closure gap:** Correction and a later fixed-reporter process executed without editing its rule. A fresh coding-agent session, rather than a Python process, was not tested.

**Acceptance to verify:** The corrected number matches the predictions. The original and correction note remain. No retained skill change is claimed.

### [07.02 · Test a reflection before trusting it](../../../rsi/07_understanding_self_star/step_02_reflection/README.md)

1. **Write a testable reflection.** Avoid treating explanation as proof.
2. **Test the rule.** Compare behavior on a new case.

**Additional change:** Compare “always use a tree” with the narrow rule on the same two checked cases. Explain any contradiction without adding undeclared fits.

**Evidence:** [Executed self-* and measurement activities with labelled replays](../../../rsi/evidence/2026-09-20/self-star-and-measurement/README.md).

**Closure gap:** Two prediction-based checks recompute existing regression/classification evidence and test the overbroad rule. These known cases are replays, not fresh reflection-validation tasks.

**Acceptance to verify:** The proposed rule has a falsifying case. Actual outcomes determine retention. The note does not rewrite the history of the failure.

### [07.03 · Retain and use a lesson](../../../rsi/07_understanding_self_star/step_03_persistent_learning/README.md)

1. **Retain the narrow rule.** Preserve scope and evidence.
2. **Apply it later.** Trace persistence into behavior.

**Additional change:** Apply the rule to a case outside its stated scope. Predict possible negative transfer before running a small check.

**Evidence:** [Executed self-* and measurement activities with labelled replays](../../../rsi/evidence/2026-09-20/self-star-and-measurement/README.md).

**Closure gap:** A separate process reads the retained rule, changes a later cached-candidate decision, and refuses a metric-scope mismatch. The no-memory control is deliberately weak; benefit does not establish LLM learning or unseen generalization.

**Acceptance to verify:** The memory version is identified. A later action is linked to a specific rule. The result distinguishes use from benefit.

### [07.04 · Improve a task skill with a fixed procedure](../../../rsi/07_understanding_self_star/step_04_self_improvement/README.md)

1. **Propose one skill edit.** Target a documented procedural weakness.
2. **Compare the skills.** Measure behavior and cost.

**Additional change:** Edit the improver itself in a separate unexecuted proposal. Explain why this creates a different experiment that needs another comparison.

**Evidence:** [Executed self-* and measurement activities with labelled replays](../../../rsi/evidence/2026-09-20/self-star-and-measurement/README.md).

**Closure gap:** The eight-fit comparison, fixed-rule checks, copied inputs, numerical examples, additional proposals, and actual rollback are retained. Cached comparisons are replays; interpreter behavior is not independent LLM behavior. Real learner assessment remains untested.

**Acceptance to verify:** The improver version remains fixed. The child is actually used. The acceptance decision follows a declared rule and preserves rejected edits.

### [07.05 · Let work reorganize under local rules](../../../rsi/07_understanding_self_star/step_05_organization/README.md)

1. **Run fixed assignment.** Create a baseline organization.
2. **Allow local reassignment.** Observe organization without changing skills.

**Additional change:** Add a shared-resource bottleneck or communication delay. Predict when dynamic reassignment loses its advantage.

**Evidence:** [Executed synthetic cases](../../../rsi/evidence/2026-09-20/organization-and-emergence/README.md).

**Closure gap:** Eight cases include overhead, random-history, and urgent-job contrasts. Map the listed outputs to each action; no real agent workers or learner responses were tested.

**Acceptance to verify:** Both runs use the same synthetic jobs and worker capabilities. The trace shows reassignment. Any speed claim is confined to this simulation.

### [07.06 · Observe a collective pattern](../../../rsi/07_understanding_self_star/step_06_emergence/README.md)

1. **Specify the pattern.** Choose an observable collective property.
2. **Remove the interaction.** Test dependence on local rules.

**Additional change:** For the optional counterexample, declare one urgent-job fixture and run it twice: once with FIFO and once with local preference. Keep both traces and compare grouping with lateness. Explain how a visible pattern can be undesirable without replacing the three main cases.

**Evidence:** [Executed synthetic cases](../../../rsi/evidence/2026-09-20/organization-and-emergence/README.md).

**Closure gap:** Eight cases include overhead, random-history, and urgent-job contrasts. Map the listed outputs to each action; no real agent workers or learner responses were tested.

**Acceptance to verify:** The pattern is defined before measurement. Local rules and global statistic are distinct. Claims remain limited to the simulation.

### [07.07 · Learn what self-play does and does not provide](../../../rsi/07_understanding_self_star/step_07_self_play/README.md)

1. **Fix the game and comparison.** Keep evaluation choices outside the learning loop.
2. **Run actual self-play learning.** Inspect a parameter change caused by a game.
3. **Inspect the frozen comparison.** Separate learning from measured benefit.
4. **Name the mechanism.** Keep the claim tied to the mutable object.

**Additional change:** Inspect the untrained baseline: it plays 500 games but retains no parameter changes. Explain why more interaction alone would not train it. Then propose, without running, a comparison against a stronger opponent and state which earlier claim that would test.

**Evidence:** [Executed policy learning](../../../rsi/evidence/2026-09-20/self-play/README.md).

**Closure gap:** Training, frozen evaluation, and parameter traces are retained. The proposed stronger-opponent comparison is a planning exercise; it has not run.

**Acceptance to verify:** All 4,000 experiment games are retained. The table has actual updates, legal game traces, and unchanged evaluation hashes. Both policies use the declared evaluation schedules. The report separates this one measured comparison from claims about optimal play, other tasks, or RSI.

### [07.08 · Make a self-modification inspectable](../../../rsi/07_understanding_self_star/step_08_modification/README.md)

1. **Apply one bounded edit.** Identify the mutable surface.
2. **Check and roll back if needed.** Separate modification from acceptance.

**Additional change:** Propose deleting a check to make more candidates pass. Explain why that changes acceptance rather than demonstrating better task performance.

**Evidence:** [Executed self-* and measurement activities with labelled replays](../../../rsi/evidence/2026-09-20/self-star-and-measurement/README.md).

**Closure gap:** The eight-fit comparison, fixed-rule checks, copied inputs, numerical examples, additional proposals, and actual rollback are retained. Cached comparisons are replays; interpreter behavior is not independent LLM behavior. Real learner assessment remains untested.

**Acceptance to verify:** The changed surface, parent, child, checks, and active version are recorded. The outcome does not receive an automatic improvement label.

## 08 · Measure what improved

### [08.01 · Distinguish a result from a reliable comparison](../../../rsi/08_measuring_improvement/step_01_repeat_measurement/README.md)

1. **Predeclare repetitions.** Prevent favorable seed selection.
2. **Run and summarize.** Show the whole distribution of outcomes.

**Additional change:** Calculate how the conclusion changes if only the best seed is shown. Label that selection as misleading.

**Evidence:** [Executed loop, routing, context, ablation, and repetition activities](../../../rsi/evidence/2026-09-20/loops-and-systems/README.md).

**Closure gap:** Six fits across all three prespecified seed pairs, checked predictions, actual-data plot, and post-hoc best-seed contrast are retained. Three seeds share one split; dataset uncertainty and learner interpretation remain untested.

**Acceptance to verify:** All six planned runs appear, or missing runs are explained. No seed is discarded. Uncertainty includes task and data limitations.

### [08.02 · Freeze selection before final evaluation](../../../rsi/08_measuring_improvement/step_02_final_boundary/README.md)

1. **Freeze the choice.** Commit before observing final outcomes.
2. **Evaluate once.** Test the lock as well as the score.

**Additional change:** Describe a separate evaluation service where the candidate cannot read cases or edit scoring. List which boundary is stronger than the local exercise.

**Evidence:** [Selected author execution](../../../rsi/evidence/2026-09-20/clean-journey/08-02).

**Closure gap:** Final lock and row/target recomputation executed. The author had seen the public final result before; this is a replay.

**Acceptance to verify:** Final evaluation uses the recorded recipe and original training rows. A later fit request is rejected. The report states that the source is public.

### [08.03 · Count the cost of research](../../../rsi/08_measuring_improvement/step_03_cost/README.md)

1. **Build the ledger.** Account for the full route to the result.
2. **Reinterpret the comparison.** Match the conclusion to available accounting.

**Additional change:** Add a large proposal-generation cost to a labelled numerical illustration. Determine when a fit-efficient method becomes more expensive overall.

**Evidence:** [Executed self-* and measurement activities with labelled replays](../../../rsi/evidence/2026-09-20/self-star-and-measurement/README.md).

**Closure gap:** The eight-fit comparison, fixed-rule checks, copied inputs, numerical examples, additional proposals, and actual rollback are retained. Cached comparisons are replays; interpreter behavior is not independent LLM behavior. Real learner assessment remains untested.

**Acceptance to verify:** The ledger reconciles every attempt. Unknown cost is distinct from zero. The report states what resource equality was actually achieved.

### [08.04 · Separate the effects of memory and procedure changes](../../../rsi/08_measuring_improvement/step_04_ablation/README.md)

1. **Declare four arms.** Separate main effects and interaction.
2. **Execute the comparison.** Retain interactions and failures.

**Additional change:** Remove one conflicting memory rule and check one affected arm in a separately declared follow-up. Keep all other conditions fixed. Preserve both memory versions and the extra check or fit cost. Do not merge this fifth result into the original four-arm experiment.

**Evidence:** [Executed self-* and measurement activities with labelled replays](../../../rsi/evidence/2026-09-20/self-star-and-measurement/README.md).

**Closure gap:** The eight-fit comparison, fixed-rule checks, copied inputs, numerical examples, additional proposals, and actual rollback are retained. Cached comparisons are replays; interpreter behavior is not independent LLM behavior. Real learner assessment remains untested.

**Acceptance to verify:** All arms are present and differ only in declared components. Shared-context limitations are stated. No favorable arm is relabelled as the only planned comparison.

### [08.05 · Test whether the lesson transfers](../../../rsi/08_measuring_improvement/step_05_transfer/README.md)

1. **Freeze and map.** Separate general procedure from task-specific facts.
2. **Run both procedures.** Observe generalization and negative transfer.

**Additional change:** Use the observed failure to propose a new skill version, but label its evaluation as a new development round requiring fresh transfer cases.

**Evidence:** [Executed self-* and measurement activities with labelled replays](../../../rsi/evidence/2026-09-20/self-star-and-measurement/README.md).

**Closure gap:** Four new fits use frozen skill hashes and a predeclared wine interface. Prior public wine outcomes were author-known, so the run is a transfer replay, not an uncontaminated transfer test. A new development proposal stays unexecuted.

**Acceptance to verify:** The procedure version is frozen before wine outcomes. Task-interface changes are documented. The result is not used to rewrite the original claim retroactively.

### [08.06 · Reject a misleading win and roll back](../../../rsi/08_measuring_improvement/step_06_rollback/README.md)

1. **Audit the win.** Recompute the metric that was promised.
2. **Reject and restore.** Keep the evidence while restoring the active version.

**Additional change:** Create a genuinely new task where overall accuracy is the chosen objective. Explain why its results belong in a separate record with a stated tradeoff.

**Evidence:** [Executed self-* and measurement activities with labelled replays](../../../rsi/evidence/2026-09-20/self-star-and-measurement/README.md).

**Closure gap:** The eight-fit comparison, fixed-rule checks, copied inputs, numerical examples, additional proposals, and actual rollback are retained. Cached comparisons are replays; interpreter behavior is not independent LLM behavior. Real learner assessment remains untested.

**Acceptance to verify:** The decision uses the predeclared metric and validity rules. Rejected artifacts remain available. No performance claim comes from changing the evaluator.

## 09 · Improve the improvement procedure

### [09.01 · Identify the solver, improver, and evaluator](../../../rsi/09_recursive_self_improvement/step_01_three_objects/README.md)

1. **Draw the boundaries.** Name the objects before classifying the result.
2. **Classify three changes.** Test the map on concrete examples.

**Additional change:** In a labelled diagram, let a candidate change the external final metric after seeing its result. Explain why that invalidates the comparison. Contrast it with a candidate improver changing its internal proposal-selection rule while the external metric, final cases, and resource budget stay fixed.

**Evidence:** [Related comparison evidence](../../../rsi/evidence/2026-09-20/clean-journey/09-05/README.md).

**Closure gap:** The matched run illustrates this mechanism. The complete lab actions and additional change have not been individually closed.

**Acceptance to verify:** The evaluator is outside the ordinary mutable surface. The map distinguishes host model, task model, task skill, and improver procedure.

### [09.02 · Run repeated improvement with an unchanged improver](../../../rsi/09_recursive_self_improvement/step_02_fixed_improver/README.md)

1. **Freeze the improver.** Make the baseline identifiable.
2. **Run two generations.** Preserve all proposals and decisions.

**Additional change:** Use a rejected child as the next parent in a labelled diagnostic replay. Explain why that would contradict the recorded promotion policy.

**Evidence:** [Two executed fixed-improver generations](../../../rsi/evidence/2026-09-20/two-generations/README.md).

**Closure gap:** Four fits, the same improver hash, one rejected task child, one accepted child, and a rejected-child replay are retained. Learner interpretation remains untested.

**Acceptance to verify:** Both rounds use the same improver. Every retained task skill has a corresponding evaluation. The conclusion says repeated self-improvement, not automatically RSI.

### [09.03 · Propose a change to the improver](../../../rsi/09_recursive_self_improvement/step_03_revise_improver/README.md)

1. **Diagnose the improver.** Target a procedural failure rather than a model setting.
2. **Create the child.** Preserve a runnable version.

**Additional change:** Compare “write more thoughtful proposals” with “test a contrasting case before promotion.” Explain which is easier to inspect and falsify.

**Evidence:** [Related comparison evidence](../../../rsi/evidence/2026-09-20/clean-journey/09-05/README.md).

**Closure gap:** The matched run illustrates this mechanism. The complete lab actions and additional change have not been individually closed.

**Acceptance to verify:** The edit affects future skill improvement. Parent and child remain available. The report does not claim effectiveness from text quality alone.

### [09.04 · Use the revised improver in the next round](../../../rsi/09_recursive_self_improvement/step_04_inherit/README.md)

1. **Start from the inherited version.** Make selection explicit.
2. **Observe the changed action.** Trace instructions into later improvement.

**Additional change:** Replace the active pointer with v0 in a labelled dry run. Identify which action should disappear and which evaluation rules remain fixed.

**Evidence:** [Related comparison evidence](../../../rsi/evidence/2026-09-20/clean-journey/09-05/README.md).

**Closure gap:** The matched run illustrates this mechanism. The complete lab actions and additional change have not been individually closed.

**Acceptance to verify:** The trace includes version identity and an observed decision difference. Merely copying the new file is not accepted as proof of use.

### [09.05 · Measure whether the revised improver helps](../../../rsi/09_recursive_self_improvement/step_05_compare_improvers/README.md)

1. **Freeze the protocol.** Define the comparison before execution.
2. **Run both arms.** Measure descendants and overhead.

**Additional change:** Show how reporting only the best child from each arm hides failed proposals and selection cost.

**Evidence:** [Selected author execution](../../../rsi/evidence/2026-09-20/clean-journey/09-05).

**Closure gap:** Eight-fit matched comparison executed. Two constructed cases, one shared author context, and unmeasured inference cost limit the result.

**Acceptance to verify:** Both arms start from the same solver. Their resource limits and known costs are reported. The conclusion concerns the tested improvers and tasks only.

### [09.06 · Run bounded recursive generations](../../../rsi/09_recursive_self_improvement/step_06_bounded_generations/README.md)

1. **Declare the lineage.** Make inheritance and limits explicit.
2. **Execute and checkpoint.** Keep every transition reviewable.

**Additional change:** Interrupt after a proposal but before promotion. Explain which version is active on resume and which evidence is still missing.

**Evidence:** [Two executed improver-comparison generations](../../../rsi/evidence/2026-09-20/two-generations/README.md).

**Closure gap:** Eight fits, proposal/resume checkpoints, ancestry checks, and third-generation refusal executed. Both improver proposals were rejected: this run does not prove an accepted revised improver governs the next generation. The protocol and state predate the run; the consolidated lineage was derived afterward.

**Acceptance to verify:** No hidden extra generation runs. Rejected versions do not become active accidentally. The total ledger includes all attempts and known costs.

### [09.07 · State the result without overstating it](../../../rsi/09_recursive_self_improvement/step_07_claim/README.md)

1. **Audit the evidence.** Match each claim to its necessary observation.
2. **Teach it back.** Test whether the distinction transfers.

**Additional change:** Remove the inheritance trace from a copy of the evidence pack. Identify which claim becomes unsupported even if the final task score stays high.

**Evidence:** [Related comparison evidence](../../../rsi/evidence/2026-09-20/clean-journey/09-05/README.md).

**Closure gap:** The matched run illustrates this mechanism. The complete lab actions and additional change have not been individually closed.

**Acceptance to verify:** Every claimed level has a corresponding artifact and measurement. Acceleration is not inferred from two favorable points. The audit states public-data and context limits.

## 10 · Read and rebuild recent research

### [10.01 · Use a framework without turning it into a ladder](../../../rsi/10_research_studio/00_reading_frontier_research/step_01_framework/README.md)

1. **Read the criteria.** Anchor terminology to the source.
2. **Classify your evidence.** Make the framework answer a concrete question.

**Additional change:** Apply Weco’s differently defined level terminology to the same cases in a separate column. Explain why equal numbers need not mean equal mechanisms.

**Evidence:** [Versioned framework and three-case evidence classification](../../../rsi/evidence/2026-09-21/research-reading/README.md).

**Closure gap:** Selected v2 definitions and historical Weco criteria are mapped separately to actual retry, memory, and inherited-improver records; three artifact identities pass. This is an author audit of scoped demonstrations, not autonomous discovery, full-paper review, general effectiveness, or learner assessment.

**Acceptance to verify:** The audit separates structural and effective improvement. Missing evidence remains visible. Level numbers are not mixed across sources.

### [10.02 · Audit a frontier announcement](../../../rsi/10_research_studio/00_reading_frontier_research/step_02_announcements/README.md)

1. **Find the original.** Keep discovery time-bounded.
2. **Trace the evidence.** Read beyond the headline.

**Additional change:** Compare the headline with an ablation or limitation in its linked paper. Explain whether the headline omits a condition.

**Evidence:** [Date-bounded discovery and primary announcement claim trail](../../../rsi/evidence/2026-09-21/research-reading/README.md).

**Closure gap:** Six explicit recent-month queries, identity/date checks, methods/results links, and a headline-to-integrity-sample comparison are retained. Original social post, website first date, pinned runnable artifact, complete costs, independent reproduction, and learner assessment remain unverified.

**Acceptance to verify:** Every technical claim has a primary source or is marked unresolved. No inaccessible post is presented as read. The date window is explicit.

### [10.03 · Choose experiments that reduce uncertainty](../../../rsi/10_research_studio/01_memory_and_exploration/step_03_exploration/README.md)

1. **Choose broad probes.** State what each attempt teaches.
2. **Focus the final attempt.** Use observed outcomes to allocate work.

**Additional change:** Compare the focused third attempt with an existing, clearly labelled duplicate run. Inspect its recipe and prediction identity, then explain what a repeat can and cannot add. If you choose to run a duplicate instead, it must replace the third fit, not become a fourth.

**Evidence:** [Executed three-fit exploration and historical duplicate comparison](../../../rsi/evidence/2026-09-21/exploration/README.md).

**Closure gap:** Two probes, a pre-fit decision, the third feature probe, and three result checks executed. The duplicate example reuses inspected historical repeats. Author context knew prior results; no task-memory file was loaded, but cold-start exploration, causal attribution, and learner understanding were not tested.

**Acceptance to verify:** The plan distinguishes broad and focused work. All attempts and costs are retained. No final test information guides exploration.

### [10.04 · Verify the outcome, then let the actor write memory](../../../rsi/10_research_studio/01_memory_and_exploration/step_04_actor_memory/README.md)

1. **Verify only the outcome.** Keep the verifier’s role narrow.
2. **Write and inspect memory.** Keep authorship explicit.

**Additional change:** Write an overbroad “always use the winning model” note and identify a case outside its evidence.

**Evidence:** [Executed memory boundaries and retained counterexamples](../../../rsi/evidence/2026-09-21/memory-labs/README.md).

**Closure gap:** One outcome check, actor-authored bounded memory, and an inspected historical counterexample are retained; zero fits. The verifier did not approve the lesson. Independent actors and learner interpretation were not tested.

**Acceptance to verify:** The verifier checks the result; the actor writes memory. Memory quality is inspected separately. No invented approval is recorded.

### [10.05 · Evaluate with memory frozen](../../../rsi/10_research_studio/01_memory_and_exploration/step_05_frozen_memory/README.md)

1. **Freeze the artifact.** Identify exactly what is evaluated.
2. **Compare without updating.** Measure the retained state.

**Additional change:** After evaluation, declare one update to a separate memory copy with zero extra fits. Compare its before/after hashes and confirm the frozen original is unchanged. Explain why measuring adaptation performance would require a separate experiment, a new budget, and declared update timing; this copy activity does not measure a performance benefit.

**Evidence:** [Executed memory boundaries and retained counterexamples](../../../rsi/evidence/2026-09-21/memory-labs/README.md).

**Closure gap:** Four fits, pre-fit decisions, frozen choices, prediction checks, and one separate adaptation-copy update executed. Both arms share author context and the same decision rule; equal scores do not isolate a memory effect. Adaptation performance, clean agent contexts, inference costs, and learner understanding remain untested.

**Acceptance to verify:** The memory stays unchanged. Resource equality and context exposure are reported. The result does not claim a full RSIAgent reproduction.

### [10.06 · Separate working state from reusable experience](../../../rsi/10_research_studio/01_memory_and_exploration/step_06_working_and_experience/README.md)

1. **Separate the stores.** Give each artifact a clear lifetime.
2. **Test retrieval.** Check what transfers to a new run.

**Additional change:** Merge both stores in a labelled copy and identify one ambiguous instruction that results.

**Evidence:** [Executed memory boundaries and retained counterexamples](../../../rsi/evidence/2026-09-21/memory-labs/README.md).

**Closure gap:** Two typed retrieval checks and a conflicting merged copy are retained; zero fits. The new and stale working states are constructed fixtures. General semantic retrieval, autonomous memory formation, and learner interpretation were not tested.

**Acceptance to verify:** The new state reflects the new task. Experience retains its evidence and scope. Stale identities are rejected.

### [10.07 · Build a tree of attempted solutions](../../../rsi/10_research_studio/02_dream_rsi/step_07_discovery_tree/README.md)

1. **Define the tree.** Make lineage explicit.
2. **Populate it with runs.** Link nodes to evidence.

**Additional change:** Add an unexecuted branch to the diagram and show it as unknown rather than assigning a schematic score.

**Evidence:** [Executed discovery, replay, and online comparison](../../../rsi/evidence/2026-09-21/dream-labs/README.md).

**Closure gap:** Three bike fits and outcome checks, a pre-fit branch decision, a measured tree, and an unexecuted proposal are retained. Recipe ancestry is a classroom simplification; no source-paper workspace inheritance, independent discovery agent, blind task, or learner assessment was tested.

**Acceptance to verify:** Parent links and trial identities agree. Failed attempts remain in the tree. No unexplored outcome is fabricated.

### [10.08 · Replay only what the history can answer](../../../rsi/10_research_studio/02_dream_rsi/step_08_replay/README.md)

1. **Generate the replay tool.** Define its evidence boundary.
2. **Compare policies.** Separate selection from new execution.

**Additional change:** Change the historical tree’s coverage by removing a node. Explain how the policy ranking can change without any new real-world evidence.

**Evidence:** [Executed discovery, replay, and online comparison](../../../rsi/evidence/2026-09-21/dream-labs/README.md).

**Closure gap:** Two primary replays, one unsupported query, and two reduced-coverage replays ran with zero fits. Removing a measured node reversed the ranking. The fixed-order interface omits the paper’s root/leaf batches and objective; no general cost-saving or learner claim follows.

**Acceptance to verify:** No new fit occurs. Unsupported paths are unknown. Cost reporting does not equate zero repeated fits with zero total cost.

### [10.09 · Test the replay winner on fresh work](../../../rsi/10_research_studio/02_dream_rsi/step_09_online/README.md)

1. **Freeze the policies.** Prevent online results from rewriting selection history.
2. **Run online.** Measure actual environment outcomes.

**Additional change:** Use online failures to propose a new policy version, then explain why it needs another fresh confirmation set.

**Evidence:** [Executed discovery, replay, and online comparison](../../../rsi/evidence/2026-09-21/dream-labs/README.md).

**Closure gap:** Four fits on new synthetic rows, frozen policies and choices, checked evaluation predictions, costs, and an unexecuted revision proposal are retained. Replay selected the existing baseline, so no accepted policy update was redeployed. Author-known task generation, agent isolation, inference cost, and learner assessment remain limitations.

**Acceptance to verify:** New outcomes are produced by actual fits. Policies remain frozen during confirmation. The conclusion reports both phases and their costs.

### [10.10 · Localize a harness problem](../../../rsi/10_research_studio/03_modular_harness_evolution/step_10_localize/README.md)

1. **Compare traces.** Find the earliest relevant divergence.
2. **Patch one component.** Test a narrow intervention.

**Additional change:** Make the same change in two components in a labelled proposal and explain why attribution becomes harder.

**Evidence:** [Executed module checks and source-specific lineage audit](../../../rsi/evidence/2026-09-21/modular-labs/README.md).

**Closure gap:** Two prerequisite trace captures and two context-only patch checks executed; a two-component alternative remains a labelled proposal. Component and fixed-driver scope is explicit. Constructed records and a stub do not test real language-model compression, independent actors, or learner understanding.

**Acceptance to verify:** The edit stays within its declared component. The retained outcome includes both target and regression checks.

### [10.11 · Integrate edits and test transfer](../../../rsi/10_research_studio/03_modular_harness_evolution/step_11_integrate/README.md)

1. **Inspect the interfaces.** Look for conflicting assumptions.
2. **Run integration and transfer.** Measure the whole combination.

**Additional change:** For the seventh execution, remove one field expected by the second component in the declared malformed fixture. Run the combined system and confirm a clear interface failure before the fit stub.

**Evidence:** [Executed module checks and source-specific lineage audit](../../../rsi/evidence/2026-09-21/modular-labs/README.md).

**Closure gap:** All seven declared fixture executions are retained, including independent-edit passes, combined failures on original/fresh cases, and a malformed-input refusal before the stub. Zero fits. The combination was rejected; broad transfer, real agents, and learner interpretation remain untested.

**Acceptance to verify:** The combined version has its own tests and identity. Transfer cases are distinguished from selection cases. Failed integration is not hidden. Seven fixture records account for the complete budget.

### [10.12 · Compare agent evolution and improver evolution](../../../rsi/10_research_studio/03_modular_harness_evolution/step_12_lineage/README.md)

1. **Read the original mechanisms.** Avoid relying on secondary labels.
2. **Map your lineage.** Apply the same questions locally.

**Additional change:** Erase the improver-version column and explain which conclusions become ambiguous.

**Evidence:** [Executed module checks and source-specific lineage audit](../../../rsi/evidence/2026-09-21/modular-labs/README.md).

**Closure gap:** Selected primary methods and both source figures were inspected. Eight local proposal edges and 28 source files were identity-checked; both improver proposals remain rejected. No new model execution, independent source reproduction, accepted recursive revision in this run, or learner assessment is established.

**Acceptance to verify:** Every historical technical assertion has a primary citation. The local classification is based on actual versions and traces.

### [10.13 · Inspect an inner ML researcher](../../../rsi/10_research_studio/04_aide2/step_13_inner_research/README.md)

1. **Define the operators.** Expose the research procedure.
2. **Run the inner search.** Save the complete search trace.

**Additional change:** Replay the same known candidate outcomes under a different ordering and state where unobserved outcomes prevent a conclusion.

**Evidence:** [Executed inner search, matched procedure comparison, and role fixtures](../../../rsi/evidence/2026-09-21/aide-labs/README.md).

**Closure gap:** Four regression fits, before-action decisions, retained and rejected recipes, prediction checks, and an unknown-stopping reordered replay executed. The fixed controller and author-exposed data do not establish autonomous discovery, protected evaluation, or learner understanding.

**Acceptance to verify:** The operator choices and budget are visible. The retained result is identifiable. The exercise is labelled a small adaptation of the nested-research idea.

### [10.14 · Improve the inner researcher under a total budget](../../../rsi/10_research_studio/04_aide2/step_14_outer_research/README.md)

1. **Propose the outer change.** Target research behavior.
2. **Compare researchers.** Count the whole nested experiment.

**Additional change:** Give the child twice the fit budget in a separate illustration and explain why that no longer isolates the procedure change.

**Evidence:** [Executed inner search, matched procedure comparison, and role fixtures](../../../rsi/evidence/2026-09-21/aide-labs/README.md).

**Closure gap:** One actor proposal and two frozen three-fit searches executed from empty matched state. An unequal-budget illustration stayed unexecuted. The child improved selection MAE on exposed development data; inference cost, independent tasks, statistical reliability, and learner understanding remain untested.

**Acceptance to verify:** Starting artifacts and declared budgets match. All nested attempts remain in the ledger. The claim is limited to this comparison.

### [10.15 · Test the ignition claim separately](../../../rsi/10_research_studio/04_aide2/step_15_ignition/README.md)

1. **Define the new outcome.** Avoid reusing the old score as proof.
2. **Run a small role-transfer test.** Inspect what the evidence can support.

**Additional change:** Construct an example where a strong optimizer always proposes overcomplicated procedures. Explain why task skill and improvement skill can diverge.

**Evidence:** [Executed inner search, matched procedure comparison, and role fixtures](../../../rsi/evidence/2026-09-21/aide-labs/README.md).

**Closure gap:** Two frozen-producer preferences were projected through one shared adapter into target procedures; six behavioral fixtures and one separate overcomplication check executed with zero fits. General researcher-code generation, independent proposer contexts, repeated fresh-task improvement, and ignition are not established.

**Acceptance to verify:** The audit does not call the paper’s ignition result established. The classroom comparison uses a new outcome rather than recycling task scores.

### [10.16 · Improve task skills with a fixed pipeline](../../../rsi/10_research_studio/05_meta_skill_evolution/step_16_task_skills/README.md)

1. **Freeze the pipeline.** Make its responsibilities visible.
2. **Update the task skill.** Measure the output of the pipeline.

**Additional change:** Rename the updater without changing its behavior. Explain why a new name supplies no new mechanism.

**Evidence:** [Executed fixed task repairs and an inherited updater revision](../../../rsi/evidence/2026-09-21/meta-skills/README.md).

**Closure gap:** Two separately allocated parent captures, one task-skill edit, two child checks, an unchanged updater, and a byte-identical renamed copy are retained. Constructed ML workflow decisions test a unit repair, not new model performance, independent agents, or learner understanding.

**Acceptance to verify:** Task and meta-skill versions are separate. Acceptance is based on executed evidence. No recursive claim is inferred from the prefix meta.

### [10.17 · Update the skill updater on a slower schedule](../../../rsi/10_research_studio/05_meta_skill_evolution/step_17_meta_skills/README.md)

1. **Revise the updater.** Use accumulated evidence at the right level.
2. **Inherit and compare.** Observe the slower change in later work.

**Additional change:** Change the update frequency in a labelled simulation and explain the tradeoff between responsiveness, cost, and attribution.

**Evidence:** [Executed fixed task repairs and an inherited updater revision](../../../rsi/evidence/2026-09-21/meta-skills/README.md).

**Closure gap:** A separately prepared second update trace, one self-directed updater proposal, and two later task-skill arms executed. The revised policy selected a different internal check; both arms faced the same three external cases. A schedule simulation is labelled hypothetical. Shared author context and known fixtures do not establish general autonomous discovery, protected evaluation, statistical benefit, or learner understanding.

**Acceptance to verify:** The update schedule and inheritance are explicit. Structural recursion and measured effectiveness are reported separately.

### [10.18 · Turn a limitation into a scientific hypothesis](../../../rsi/10_research_studio/06_scientist_two/step_18_hypothesis/README.md)

1. **Write the hypothesis.** Connect a limitation to a measurable consequence.
2. **Run the experiment.** Produce evidence for the stated question.

**Additional change:** Rewrite “weather improves demand prediction” as a conditional statement tied to this task, model, period, and metric.

**Evidence:** [Executed scientific workflow and audited result lineage](../../../rsi/evidence/2026-09-21/scientist-labs/README.md).

**Closure gap:** A saved hypothesis, two matched fits, prediction checks, hourly errors, and a conditional conclusion are retained. The author had prior development-result exposure; this is not blind hypothesis discovery, causal evidence, or learner assessment.

**Acceptance to verify:** The hypothesis precedes results. One declared factor changes. A failed hypothesis remains a valid research outcome.

### [10.19 · Screen ideas and test their contributions](../../../rsi/10_research_studio/06_scientist_two/step_19_screen_ablate/README.md)

1. **Declare the screen.** Specify what the cheap test can establish.
2. **Confirm and ablate.** Test the selected contribution.

**Additional change:** Select on the fastest screen only and explain why that could miss an idea whose benefit appears at a larger data scale.

**Evidence:** [Executed scientific workflow and audited result lineage](../../../rsi/evidence/2026-09-21/scientist-labs/README.md).

**Closure gap:** Two separately implemented subset screens and two matched fuller confirmation/ablation fits executed. The fastest-screen alternative uses measured times without extra fits. No fuller-condition ranking of the unselected idea, protected evaluation, independent-agent screening, or learner assessment is established.

**Acceptance to verify:** The screen does not consume final evaluation. Confirmation and ablation use matched conditions. All ideas and costs are retained.

### [10.20 · Answer a criticism with evidence](../../../rsi/10_research_studio/06_scientist_two/step_20_review_rebuttal/README.md)

1. **Review the claim.** Identify one consequential weakness.
2. **Respond through a test.** Let new evidence change the conclusion.

**Additional change:** Write a response that only restates the original claim. Explain which uncertainty remains unchanged.

**Evidence:** [Executed scientific workflow and audited result lineage](../../../rsi/evidence/2026-09-21/scientist-labs/README.md).

**Closure gap:** A current-context agent review, frozen two-fit seed follow-up, evidence-linked response, and restatement counterexample are retained. Two seeds do not establish broad robustness; independent peer review, conference acceptance, and learner assessment remain absent.

**Acceptance to verify:** The response cites actual new evidence or identifies an unresolved issue. No automated score is presented as human peer acceptance.

### [10.21 · Distinguish better discoveries from a better scientist](../../../rsi/10_research_studio/06_scientist_two/step_21_successive_results/README.md)

1. **Trace successive results.** Separate artifacts from their producer.
2. **Audit the claim.** Apply the same standard to local and paper-reported work.

**Additional change:** Propose a matched experiment where old and new researcher procedures start from the same fresh baseline.

**Evidence:** [Executed scientific workflow and audited result lineage](../../../rsi/evidence/2026-09-21/scientist-labs/README.md).

**Closure gap:** The two-study lineage records a fixed researcher hash with growing context, actual costs, a measured chart, selected source evaluation audit, and an unexecuted matched researcher comparison. It does not demonstrate a revised improver, researcher-level superiority, or learner understanding.

**Acceptance to verify:** The audit names the evaluated object. It does not infer researcher self-improvement from successive task gains alone.

### [10.22 · Turn a researcher correction into a task](../../../rsi/10_research_studio/07_sciencebuddy/step_22_human_task/README.md)

1. **Extract the requirement.** Retain the human-origin distinction.
2. **Test the rubric.** Compare a complete and incomplete report.

**Additional change:** Read a small GWAS example at the conceptual level: genetic variants are tested for association with a trait. Explain why statistical association is not a causal or clinical recommendation and why domain review is still needed.

**Evidence:** [Executed local ScienceBuddy teaching activities](../../../rsi/evidence/2026-09-20/sciencebuddy-laptop/README.md).

**Closure gap:** Report checks, toy numerical updates, synthetic pair transitions, source arithmetic, and additional reading/planning notes are retained. The reporter is deterministic and author-written; no independent agent behavior, real LLM training, paper reproduction, or learner assessment is established.

**Acceptance to verify:** Fixture origin is explicit. Criteria connect to observable evidence. The test does not claim domain-expert validation.

### [10.23 · Adapt the harness to the rubric](../../../rsi/10_research_studio/07_sciencebuddy/step_23_harness_adaptation/README.md)

1. **Revise the procedure.** Target the observed omission.
2. **Run the rubric checks.** Measure the revised behavior.

**Additional change:** Make the child skill longer without adding a useful requirement. Explain why more instructions need not improve the result.

**Evidence:** [Executed local ScienceBuddy teaching activities](../../../rsi/evidence/2026-09-20/sciencebuddy-laptop/README.md).

**Closure gap:** Report checks, toy numerical updates, synthetic pair transitions, source arithmetic, and additional reading/planning notes are retained. The reporter is deterministic and author-written; no independent agent behavior, real LLM training, paper reproduction, or learner assessment is established.

**Acceptance to verify:** The report names a harness change and does not claim a weight update. Both positive and negative rubric cases are exercised.

### [10.24 · See what grouped rewards contribute](../../../rsi/10_research_studio/07_sciencebuddy/step_24_grpo/README.md)

1. **Calculate advantages.** Expose the signal behind the update.
2. **Test edge cases.** Make the limits concrete.

**Additional change:** Use the scale skill to draft, without launching, a real training checklist: source implementation, model license, rollout data, reward validation, GPU memory, optimizer, checkpoints, and held-out evaluation.

**Evidence:** [Executed local ScienceBuddy teaching activities](../../../rsi/evidence/2026-09-20/sciencebuddy-laptop/README.md).

**Closure gap:** Report checks, toy numerical updates, synthetic pair transitions, source arithmetic, and additional reading/planning notes are retained. The reporter is deterministic and author-written; no independent agent behavior, real LLM training, paper reproduction, or learner assessment is established.

**Acceptance to verify:** The calculation is reproducible and handles zero variance. No LLM checkpoint is claimed. The report lists missing pieces of real training.

### [10.25 · Track model–harness pairs across cycles](../../../rsi/10_research_studio/07_sciencebuddy/step_25_coevolution/README.md)

1. **Define paired state.** Avoid mixing incompatible versions.
2. **Simulate the cycle.** Track what changes at each stage.

**Additional change:** Draft a larger-compute extension that replaces the placeholder with real training and specifies how checkpoints, rewards, and paired evaluation would be recorded.

**Evidence:** [Executed local ScienceBuddy teaching activities](../../../rsi/evidence/2026-09-20/sciencebuddy-laptop/README.md).

**Closure gap:** Report checks, toy numerical updates, synthetic pair transitions, source arithmetic, and additional reading/planning notes are retained. The reporter is deterministic and author-written; no independent agent behavior, real LLM training, paper reproduction, or learner assessment is established.

**Acceptance to verify:** Every simulated result names both versions. Synthetic values are never mixed with paper or classroom measurements. The fixed reflector and feedback-source distinctions are checked against the paper.

### [10.26 · Read the ScienceBuddy results precisely](../../../rsi/10_research_studio/07_sciencebuddy/step_26_audit_results/README.md)

1. **Reconstruct the comparison.** Read definitions beside numbers.
2. **Audit the mechanism claim.** Separate changed and fixed components.

**Additional change:** Rewrite an overbroad headline as a source-scoped statement including task family, metric, and reported-evidence status.

**Evidence:** [Executed local ScienceBuddy teaching activities](../../../rsi/evidence/2026-09-20/sciencebuddy-laptop/README.md).

**Closure gap:** Report checks, toy numerical updates, synthetic pair transitions, source arithmetic, and additional reading/planning notes are retained. The reporter is deterministic and author-written; no independent agent behavior, real LLM training, paper reproduction, or learner assessment is established.

**Acceptance to verify:** The audit reports 31.1 percentage points correctly. It does not mix coverage, validation, and held-out single-attempt metrics. Feedback sources are not all called human.

### [10.27 · Keep traces, knowledge, and active skills separate](../../../rsi/10_research_studio/08_skills_and_procedures/step_27_wiki/README.md)

1. **Separate the artifacts.** Give each store its own job.
2. **Reject without forgetting.** Test the retention rule.

**Additional change:** Let the task actor read the notebook in a separate condition and explain why it changes the evaluated inference interface.

**Evidence:** [Executed knowledge retention and memory-representation checks](../../../rsi/evidence/2026-09-21/memory-interfaces/README.md).

**Closure gap:** A real prior failed proposal, immutable-by-procedure trace, persistent notebook versions, and unchanged active skill are retained. Two candidate checks reject the fallback; a separate exposure-only condition reads the notebook without a third task check. Scripted input identities do not establish isolated coding-agent access or general skill-evolution benefit.

**Acceptance to verify:** The rejected skill is not active. The notebook retains evidence-linked learning. Role access is labelled as an instruction unless technically enforced.

### [10.28 · Refine a procedure graph](../../../rsi/10_research_studio/08_skills_and_procedures/step_28_procedural_graph/README.md)

1. **Localize the procedure.** Show only guidance needed for the next action.
2. **Refine one transition.** Test the change before promotion.

**Additional change:** For the fourth check, introduce a validly typed but semantically wrong feature and execute the domain check. Explain why a procedure graph still needs meaning rules.

**Evidence:** [Executed procedure-graph fixtures](../../../rsi/evidence/2026-09-21/procedure-graph/README.md).

**Closure gap:** One edge edit, two parent/child selection pairs, one frozen distinct fixture, and one semantic check executed in six traversals with zero fits. Author-constructed deterministic cases are not independent LLM adaptation, blinded transfer, or learner assessment.

**Acceptance to verify:** The edited graph actually runs. Its test result is not replaced by the best intermediate selection score. Ontology and procedure remain separate.

### [10.29 · Repair a skill for an experiment-results page](../../../rsi/10_research_studio/08_skills_and_procedures/step_29_gui/README.md)

1. **Create and attempt the task.** Make the interface small and inspectable.
2. **Critique and revise.** Give the critic a defined evidence packet.

**Additional change:** Inspect the two saved UI attempts. Determine whether each inspected the warning hidden in the detail view before selecting. Do not add a third UI attempt to improve the presentation.

**Evidence:** [Two live browser attempts with saved metrics and screenshots](../../../rsi/evidence/2026-09-21/gui-skill/README.md).

**Closure gap:** The deliberate first control failed; detail inspection on the unchanged page led to a passing second selection. The visible-trace critique, one-instruction repair, exact checks, and warning-exposure audit are retained. All roles share author context; independent critique, general skill reuse, other browser integrations, and learner assessment remain untested.

**Acceptance to verify:** The page uses actual data. Live interaction is distinguished from reading HTML or a simulation. Missing browser capability is reported rather than claiming completion.

### [10.30 · Reduce cost without hiding quality loss](../../../rsi/10_research_studio/09_efficient_harnesses/step_30_cost_quality/README.md)

1. **Set the acceptance rule.** Prevent cost savings from weakening the task.
2. **Compare variants.** Count the work needed to obtain each result.

**Additional change:** Run one labelled fixture with a necessary checker removed and a fit stub in place of training. Compare its missing evidence with the declared quality floor. Explain why the apparent saving is not a valid win.

**Evidence:** [Four matched fits with fixed quality and report-cost gates](../../../rsi/evidence/2026-09-21/efficient-harnesses/README.md).

**Closure gap:** Both task pairs pass fixed floors and have identical predictions; duplicate report calls/bytes fall. The checker-removal fit stub fails, and optional source cost boundaries are audited. One-shot timings, unknown design/inference costs, shared author context, and unattempted learner assessment limit the conclusion; no paper mechanism or recursive compounding was reproduced.

**Acceptance to verify:** The acceptance rule is unchanged. All relevant costs are included or marked unknown. The conclusion is limited to measured efficiency.

### [10.31 · Compare harness generation and harness improvement](../../../rsi/10_research_studio/09_efficient_harnesses/step_31_harness_builders/README.md)

1. **Read and map the methods.** Identify the changed object in each source.
2. **Run a bounded local analogue.** Keep the changed object explicit.

**Additional change:** Propose a generator comparison on two fresh briefs. Explain why evaluating only one generated artifact is weak evidence for a general builder claim.

**Evidence:** [Source-specific map and two matched generated-harness executions](../../../rsi/evidence/2026-09-21/harness-builder/README.md).

**Closure gap:** The observed parent report failure is repaired by one component edit; child reports both recalls with identical predictions. Historical builder identity is recovered and unchanged; it does not run. The two-brief comparison is an unexecuted proposal. Independent creator/executor contexts, generator superiority, broad transfer, and learner assessment remain untested.

**Acceptance to verify:** The source audit is completed before paper-specific mechanism claims. The local experiment identifies what changed and what was evaluated.

### [10.32 · Compare raw history and summarized memory](../../../rsi/10_research_studio/10_feedback_and_transfer/step_32_memory_interface/README.md)

1. **Build an exact task.** Give the comparison an executable ground truth.
2. **Compare representations.** Measure retrieval and summary failure.

**Additional change:** Increase irrelevant event descriptions while keeping state changes fixed. Measure whether the representation effect changes.

**Evidence:** [Executed knowledge retention and memory-representation checks](../../../rsi/evidence/2026-09-21/memory-interfaces/README.md).

**Closure gap:** Five packets, five actual author answers, exact original-event checks, and an expanded-description operation audit are retained. The faulty summary implies the wrong state. All conditions share a knowledgeable author; provider costs, clean context isolation, broad memory effects, learner assessment, and parameter training are untested.

**Acceptance to verify:** The checker uses original events. Correct and faulty summaries are distinguished. The report does not claim model training or a full S3Gym reproduction.

### [10.33 · Compare action hints and richer observations](../../../rsi/10_research_studio/10_feedback_and_transfer/step_33_scaffolding/README.md)

1. **Create two kinds of help.** Avoid mixing instruction and observation.
2. **Remove the scaffold.** Inspect dependence on assistance.

**Additional change:** Give a stale action hint while preserving correct observations. Observe which condition can recover.

**Evidence:** [Four executed agent-operated form attempts](../../../rsi/evidence/2026-09-21/scaffolding/README.md).

**Closure gap:** Action-hint, richer-observation, changed unassisted, and stale-hint conditions passed exact checks. The stale detour was preplanned; all fixtures were author-known in one context. No weight training, causal scaffold comparison, independent-agent evaluation, or learner assessment occurred.

**Acceptance to verify:** The assistance types are explicit. The unassisted task is fresh and its limits are stated. The paper’s training claim is not transferred to the toy run.

### [10.34 · Keep model training aligned with its harness](../../../rsi/10_research_studio/10_feedback_and_transfer/step_34_model_harness_fit/README.md)

1. **Expose the mismatch.** Make compatibility executable.
2. **Repair locally and audit the source.** Connect the toy idea to the actual study carefully.

**Additional change:** Replace the whole correct response with another expert’s incompatible template. Explain why globally imitating a good trajectory can break a local contract.

**Evidence:** [Executed interface comparison and source audit](../../../rsi/evidence/2026-09-21/model-harness-fit/README.md).

**Closure gap:** Four parser subprocesses and unchanged hashes demonstrate format repair only. Selected primary-method reading is recorded; no weight training, source reproduction, native-agent portability, or learner assessment was tested.

**Acceptance to verify:** The parser failure and repair are executed. The source audit distinguishes parameter training from an interface demonstration.

### [10.35 · Compose changes to data, harness, and model](../../../rsi/10_research_studio/11_composition_and_reference_learning/step_35_metarsi/README.md)

1. **Define typed operators.** Make each mutable surface visible.
2. **Revise the schedule.** Trace a meta-level change into later work.

**Additional change:** Read the paper’s same-start improver comparison and per-term gains. Explain why rising cumulative gains can coexist with declining gains per term.

**Evidence:** [Executed typed-operator and scheduler simulation](../../../rsi/evidence/2026-09-21/operator-composition/README.md).

**Closure gap:** Five checks, twelve operator attempts, one policy gate, and three synthetic scores executed; a saved rule governed later work. Selected source comparison is read. No actual model training, later-task original/revised comparison, autonomous adaptation, or learner assessment was tested.

**Acceptance to verify:** The simulator enforces declared surfaces and evidence versions. Synthetic outcomes are not presented as the paper’s results. The audit distinguishes schedule composition from real model training.

### [10.36 · Diagnose failures with checked reference trajectories](../../../rsi/10_research_studio/11_composition_and_reference_learning/step_36_harnessevolve/README.md)

1. **Check the reference.** Reject a shortcut before using it as teaching evidence.
2. **Diagnose and gate an edit.** Keep the improvement general and nonregressing.

**Additional change:** Supply a legitimate alternative successful path. Explain why the first divergence is a diagnostic lead, not automatic proof that the failed path’s differing action was wrong.

**Evidence:** [Executed reference gates and candidate fixtures](../../../rsi/evidence/2026-09-21/checked-reference/README.md).

**Closure gap:** Four instrumented traces, one quality gate, and two candidate evaluations executed. Author-known deterministic fixtures, a tiny declarative skill, and trusted instrumentation do not establish independent agent learning, general leakage detection, or learner understanding.

**Acceptance to verify:** The reference is validated independently of its final answer text. The active skill does not copy case-specific answers. Both current and prior cases are evaluated.

### [10.37 · Compare systems without flattening their differences](../../../rsi/10_research_studio/12_evidence_and_open_questions/step_37_compare_systems/README.md)

1. **Build the comparison.** Use dimensions rather than a forced ranking.
2. **Challenge one classification.** Test whether the evidence supports the label.

**Additional change:** Remove performance columns and compare mechanisms alone, then restore results with their protocols. Explain why both views are useful.

**Evidence:** [Six-system source comparison and checked local claim challenge](../../../rsi/evidence/2026-09-21/system-comparison/README.md).

**Closure gap:** Mechanism-only and result views retain source versions, boundaries, resources, and reading depth. Four active local identities were checked; both improver proposals remain rejected. No source reproduction, raw paper-log audit, complete cost reconciliation, independent context, or learner assessment occurred.

**Acceptance to verify:** All technical entries have sources or an unresolved label. The matrix does not treat local demonstrations as reproductions of frontier results.

### [10.38 · Reason about bottlenecks and acceleration](../../../rsi/10_research_studio/12_evidence_and_open_questions/step_38_economics/README.md)

1. **Model the bottleneck.** Make assumptions visible.
2. **Audit acceleration.** Require evidence for the rate claim.

**Additional change:** Add a saturation limit or a more expensive verifier. Explain how either can slow later gains even when the improver becomes more capable.

**Evidence:** [Five numerical scenarios and a recorded-lineage acceleration audit](../../../rsi/evidence/2026-09-21/bottlenecks/README.md).

**Closure gap:** Calculator inputs, outputs, costlier-verifier extension, separate shrinking-increment arithmetic, copied local lineage/cost rows, and selected source assumptions are retained. No new fits or empirical acceleration follow. Total-resource cost, source-model calibration, and learner assessment remain unestablished; the separate lab-10.37 matrix now has its own evidence mapping.

**Acceptance to verify:** Synthetic values are labelled. The calculation uses total time. The final claim separates theory, reported research, and local measurements.

## 11 · Build, transfer, and explain

### [11.01 · Build a harness for a new prediction brief](../../../rsi/11_capstones/step_01_new_harness/README.md)

1. **Write and review the brief.** Make the new task scientifically coherent.
2. **Generate and prove the harness.** Deliver behavior as well as files.

**Additional change:** Use scale-experiment to prepare a larger-job plan with resources, cancellation, checkpoints, and cost limits. Label it generated-only until tested on that backend.

**Evidence:** [Generated white-wine regression harness and fresh-environment baseline](../../../rsi/evidence/2026-09-21/capstone-harness/README.md).

**Closure gap:** Two allocated actual fits, independent prediction checks, three invalid requests, seven altered-output checks, and one charged no-training failure stub are retained. Fresh dependencies reproduce prediction bytes. Larger-job plan is generated-only; peer/learner, native-agent, remote-backend, and final-evaluation checks were not performed.

**Acceptance to verify:** The handoff is sufficient, evidence is actual, and the refusal is meaningful. A different dataset alone does not establish transfer of every learned procedure.

### [11.02 · Run and audit a bounded recursive experiment](../../../rsi/11_capstones/step_02_recursive_experiment/README.md)

1. **Predeclare the experiment.** Prevent claims from following favorable accidents.
2. **Run and audit.** Keep the complete lineage.

**Additional change:** Ask a reviewer to remove one key artifact from the evidence pack and identify which claim no longer follows.

**Evidence:** [Eight-fit improver comparison with terminal evaluation](../../../rsi/evidence/2026-09-21/capstone-recursion/README.md).

**Closure gap:** Two initial fits expose the weak training-ranking rule; two matched three-fit arms execute original and revised Markdown instructions. Candidate-trial inheritance, frozen external acceptance, terminal evaluation, 43 checks and three refusals are retained. No post-acceptance third generation, autonomous proposal, fresh-task effectiveness, complete research cost, independent context, peer or learner assessment occurred.

**Acceptance to verify:** The improved object is identified. The revised improver actually governs later work. Fairness limits and missing costs remain in the conclusion.

### [11.03 · Test transfer and portability separately](../../../rsi/11_capstones/step_03_portability/README.md)

1. **Define the matrix.** Separate compatibility questions.
2. **Execute and record.** Replace intended support with evidence.

**Additional change:** Remove one host capability, such as command execution, and identify which lesson outcomes can no longer be completed.

**Evidence:** [Two-task smoke runs and a declared-capability refusal](../../../rsi/evidence/2026-09-21/capstone-portability/README.md).

**Closure gap:** Bike regression and wine classification execute through one canonical skill and shared host; result checks, both recalls, new-process comparison, four invalid requests and two capability fixtures are retained. This tests existing task adapters, not transfer of the revised improver. Another real agent, native discovery, actual permission removal, cluster cancellation/resume, total inference costs and learner assessment remain untested. Public inspection exposes final-data summaries, not final performance.

**Acceptance to verify:** Every support claim corresponds to a run. Task transfer, agent compatibility, and backend compatibility are not merged into one label.

### [11.04 · Audit an unfamiliar RSI claim](../../../rsi/11_capstones/step_04_external_audit/README.md)

1. **Read the primary evidence.** Build a source trail.
2. **Write the audit.** Make the next step testable.

**Additional change:** State the strongest reasonable interpretation of the authors’ result before presenting your limitation. Check that both can be true.

**Evidence:** [Versioned primary-source audit and acceptance-rule arithmetic](../../../rsi/evidence/2026-09-22/external-audit/README.md).

**Closure gap:** Date-bounded queries, selected v2 methods/results/limits, pinned repository metadata, a charitable short audit and a discriminating follow-up are retained. One calculator enumerates 441 count pairs with six checks. No source-system execution, raw paper-outcome reanalysis, full implementation audit, complete-paper review, independent peer or learner assessment occurred; HTML and PDF-image access failures remain explicit.

**Acceptance to verify:** The audit uses primary sources and accurate dates. It neither exaggerates nor dismisses results beyond the evidence.

### [11.05 · Teach the mechanism and defend the evidence](../../../rsi/11_capstones/step_05_teach_back/README.md)

1. **Assemble the handoff.** Make the evidence navigable.
2. **Teach and reproduce.** Test understanding beyond memorized wording.

**Additional change:** Ask the peer to propose a different prediction task. Explain what should transfer and what must be redesigned before running it.

**Evidence:** [Evidence-linked portfolio and prepared peer handoff](../../../rsi/evidence/2026-09-22/portfolio/README.md).

**Closure gap:** A no-fit assembly audit verifies thirty original identities, one concrete prediction row, matching start bytes and later instruction use. Public portfolio, existing illustration, failure story, separate costs and a one-fit peer guide are complete as author artifacts. Peer reproduction, actual learner answers, feedback and transfer proposal remain explicitly pending; this mapping does not represent a completed peer session.

**Acceptance to verify:** The portfolio has runnable evidence and a failed case. The teach-back explains the solver/improver distinction and names remaining uncertainty. Pending peer review is honestly marked.
