// Teaching support for self-* mechanisms, evidence, and recursive improvement.
export const improvementGuidance = {
  '07.01': {
    example:'An illustrative report says MAE is 12, but the saved absolute errors are 10, 20, and 30. Their mean is 20. Replacing 12 with 20 corrects this report. It does not automatically change the procedure that writes the next report, even if the correction remains in this chat.',
    outputs:[['Original and corrected reports','Preserve the incorrect claim and the evidence-backed replacement.'],['Metric recomputation','Uses the same predictions, targets, and rows as the report.'],['Correction note','Names the changed output and confirms that no reusable procedure was revised.']],
    recovery:'If the recomputed number differs from both reports, first align prediction rows with target rows and check the metric definition. Do not select the number that looks more favorable. If the agent also edits a saved skill, record that as a separate retained change; it is no longer only the correction experiment.',
    hint:'Ask what changed now and what a later session would actually read. A corrected answer and a retained prevention rule have different lifetimes.'
  },
  '07.02': {
    example:'A deep tree fits the training data exactly but has poor selection MAE. “Always avoid trees” is too broad: the failure could depend on depth, sample size, or noise. A narrower hypothesis is to compare a bounded-depth tree before using an unpruned one. A case with a real nonlinear pattern can test whether the broad advice throws away useful structure.',
    outputs:[['REFLECTION.md','Separates observed failure, proposed cause, alternative explanation, and bounded future rule.'],['Two predeclared checks','Include a case expected to help and a case that could expose harm.'],['Retention decision','Uses both outcomes and preserves a rejected explanation.']],
    recovery:'If the note claims a cause from one correlation, rewrite that sentence as a hypothesis and specify what could contradict it. If both checks reuse the exact evidence that inspired the rule, acknowledge the lack of a new test. Keep the two-check budget; further diagnoses need a separate declared follow-up.',
    hint:'Underline what the trace proves. Circle what the author inferred. The test must challenge the circled statement, not merely repeat the observed failure.'
  },
  '07.03': {
    outputs:[['MEMORY-v1.md','Retains the rule, scope, limits, and supporting evidence.'],['Later decision trace','Names the memory version and the specific action it changed before execution.'],['Use and outcome report','Distinguishes retrieval, behavior change, measured benefit, and any unexecuted no-memory counterfactual.']],
    recovery:'If the later answer only quotes the memory, identify an actual changed choice before calling it behavioral use. If a fresh session is unavailable, label the shared context. If no no-memory run exists, keep the stated alternative as a prediction; do not invent a measured baseline or infer benefit solely from reading the note.',
    hint:'There are three separate questions: was it saved, was it used, and did using it help? Find different evidence for each.'
  },
  '07.04': {
    example:'The parent research skill chooses its second model immediately after the first score. A child requires an error-slice review before that choice. Give both the same initial task and two fits. The improver that proposed this edit stays unchanged. The child can choose a better model, waste effort, or make the same decision; all three are possible outcomes.',
    outputs:[['Parent and child task skills','Show the one changed research instruction and its motivating failure.'],['Fixed improver hash','Identifies the same improvement procedure before and after the comparison.'],['Four-fit comparison and decision','Retains choices, scores, known costs, rejected candidates, and the declared acceptance rule.']],
    recovery:'If the child receives extra fits, the equal-fit comparison has changed. Preserve that run and narrow the claim rather than omitting its extra work. If both versions use the same chat, record context leakage as a limitation. If the improver also changes, separate its revision from this fixed-improver experiment.',
    hint:'Follow the edit to its target. A better task-research instruction does not show that the instruction-writing procedure became better.'
  },
  '07.05': {
    outputs:[['Synthetic job specification','Fixes six jobs, durations, expected outputs, and two worker capabilities.'],['Fixed and dynamic event traces','Show assignments, start/finish times, and every completed job.'],['Comparison and overhead case','Report completion time separately from lost, duplicate, or incorrect work; label synthetic timing.']],
    recovery:'If dynamic routing looks faster because it skipped a job, reconcile job IDs before interpreting time. If the simulation uses random durations, reuse the same generated jobs across policies. If communication delay was added only to one policy, state that assumption and explain why it is part of that policy’s modeled cost.',
    hint:'Keep the work and workers fixed. The property under test is who receives which job, not whether a worker learned a better way to do it.'
  },
  '07.06': {
    outputs:[['Pattern definition','States the clustering statistic before inspecting traces.'],['Three simulation traces','Compare local preference, no preference, and randomized history on the same jobs.'],['Pattern and lateness report','Separates grouping, completion time, and deadline failures, including any counterexample.']],
    recovery:'If every policy groups the jobs, inspect whether the input order already contains groups. If the preferred-type policy improves the clustering score while missing deadlines, retain both observations. Do not redefine emergence to mean whichever metric improved. The optional lateness pair is a new declared job fixture, not a replacement for the original comparison.',
    hint:'Name the collective pattern first. Then ask whether it depends on the interaction and whether it helps the task; these are separate claims.'
  },
  '07.07': {
    example:'In the saved author run, training game 0 ends in an O win. X’s first center move changes from value 0 to −0.2; O’s first move changes from 0 to +0.2. Each value moves 20% toward its player’s return. This does not prove the center is bad: the return includes everything that happened afterward. Later experience can revise the value.',
    outputs:[['RUN-CONTRACT.md and policy tables','Record the fixed training settings, initial zero policy, learned values, and freeze hash.'],['Training games and updates','Connect every state, action, terminal return, and changed parameter.'],['Evaluation counts, moves, and hashes','Retain wins/draws/losses by seat, actual failures, and unchanged policy bytes during evaluation.'],['SELF-PLAY-REPORT.md and measured plot','Explain the result, the untrained no-update counterexample, costs, and why the fixed trainer does not establish RSI.']],
    recovery:'A header-only initial-policy.csv is intentional: absent entries have value zero. If evaluation changes the table hash, stop interpreting its score and preserve the run for diagnosis. If the tool refuses a nonempty output directory, choose a new folder; do not overwrite prior evidence. A weak result against random play is still a valid result when rules and traces check out.',
    hint:'Point to an actual before/after table value. Then point to the unchanged code that updates it. Those two objects keep learning and recursive improvement distinct.'
  },
  '07.08': {
    example:'An agent changes its learner-owned skill from “report the model score” to “recompute the score from saved predictions before reporting.” That is an inspectable self-modification of its instructions. If the new check rejects a valid result because it aligns rows incorrectly, the modification is real but harmful. Restore the parent while retaining the child and failure.',
    outputs:[['Parent/child skill files and change note','Identify the agent-owned surface, exact edit, and reason.'],['Two check outcomes','Cover a valid case and the failure that motivated the edit.'],['Active-version record','Shows which version remains active and links any rejected child to its evidence.']],
    recovery:'If the agent edits a canonical course skill, preserve the diff and move the experiment to a learner-owned copy. If it removes an external success criterion to make the child pass, reject that comparison. An internal selection change is a different candidate procedure; it still needs unchanged external evaluation.',
    hint:'Self-modification answers “what can change?” Improvement answers “did that change help under the declared test?” Neither word supplies the other’s evidence.'
  },
  '08.01': {
    example:'Suppose the illustrative paired differences, forest MAE minus tree MAE, are −8, +2, and −6. The mean is −4: forest is better on average because lower MAE is better. The positive pair still matters. Showing only −8 would hide instability, and all three pairs still use only one dataset and partition.',
    outputs:[['Repetition plan','Freezes two recipes, calendar inputs, the split, MAE, and seeds 17, 29, and 43.'],['Six run records and paired plot','Keep every attempted pair, signs, failures, and actual measured costs.'],['Uncertainty statement','Separates seed variation from uncertainty about tasks, data, and model choices.']],
    recovery:'If a paired difference has an unclear sign, write the subtraction order and metric direction beside the table. If one fit fails, retain the missing pair and report why; do not replace its seed after seeing the other scores. Identical predictions across seeds can be correct for a deterministic operation, not proof of universal stability.',
    hint:'Ask what varied and what never varied. Repeating seeds cannot answer a question about a dataset that was never changed.'
  },
  '08.02': {
    example:'You choose candidate 2 because it has the smallest selection MAE and record that decision. Its final MAE is worse than expected. Trying candidate 3 on the same final rows to recover a pleasing score would turn those rows into selection feedback. The correct record keeps candidate 2’s result and closes this experiment.',
    outputs:[['SELECTION-DECISION.md in the lesson notes','Names the chosen recipe and the original experiment before final feedback.'],['FINAL.md and final predictions in that experiment','Retain the one final refit and metric under the existing contract.'],['Post-final refusal','Shows that a later fit request did not consume another fit or reopen selection.']],
    recovery:'If the original experiment is already closed, inspect its preserved final record and label this as a review; do not unlock it for the lesson. If the current tool source differs from its pinned source, use the original checkout. If final scoring fails after locking, investigate a diagnostic copy while preserving the closed original.',
    hint:'The important boundary is information use. Ask whether the final outcome could influence another choice in the same claimed experiment.'
  },
  '08.03': {
    example:'In a labelled numerical illustration, procedure A uses 20 fit-seconds and 100 proposal-seconds; B uses 30 and 10. A is cheaper in fitting but costs 120 measured seconds against B’s 40 if those stages are sequential. Neither number includes unknown provider charges. State the resource and assumptions before naming a winner.',
    outputs:[['COST.md for both procedures','Reconciles proposals, fits, checks, failures, retries, final evaluation, and unknown categories.'],['Attempt-to-cost mapping','Links each ledger item to a measurement or an explicit missing value.'],['Revised efficiency claim','Names the quality measure and the resource actually matched or compared.']],
    recovery:'If totals are smaller than their components, check units, overlapping parallel work, and whether wall time was added to included fit time. Avoid double counting. If provider usage is unavailable, leave it unknown rather than estimating it from a local duration. A comparison can still report equal fits without claiming equal total cost.',
    hint:'A stopwatch, a token counter, and a bill answer different questions. Keep their units and missing categories visible.'
  },
  '08.04': {
    outputs:[['ABLATION-PLAN.md','Freezes all four memory/skill combinations, inputs, metric, and per-arm budget.'],['Four decision and outcome records','Include context boundaries, failures, and measured costs.'],['Effect comparison','Compares memory within each skill version and skill change within each memory condition.']],
    recovery:'If one arm inherits an earlier arm’s conclusions through shared context, record that limitation before interpreting attribution. Fresh folders isolate artifacts, not the coding agent’s knowledge. If an arm crashes, retain the failure as an outcome. A repaired or newly edited memory is a follow-up, not a hidden substitution into the original four arms.',
    hint:'Compare memory on versus off twice: once for the parent, once for the child. Different effects reveal an interaction.'
  },
  '08.05': {
    example:'A bike-derived rule says “prefer the lowest error.” Before the wine run, you map that interface to maximizing balanced accuracy while preserving the rule’s principle of using the declared metric. Changing the candidate policy after viewing wine failures is different: the target task has now supplied development feedback.',
    outputs:[['Frozen skill hashes and interface map','Separate reusable procedure from predeclared target, metric, and model-interface changes.'],['Four wine fit records','Give each procedure two attempts under the same classification contract.'],['Transfer report','Includes balanced accuracy, both class recalls, known costs, and any harmful transfer.']],
    recovery:'If the skill contains bike-only features, record the incompatibility before execution and decide the required interface adaptation openly. If wine outcomes were already used to write the skill, call this development or replay, not an unseen transfer test. Preserve failed transfer instead of quietly rewriting the candidate to make it succeed.',
    hint:'Separate a predeclared adapter from a result-informed edit. Only the latter uses the transfer outcome to create a new procedure.'
  },
  '08.06': {
    example:'A report celebrates an always-negative classifier’s high ordinary accuracy. Its positive recall is zero and negative recall is one, so balanced accuracy is 0.5. Under the wine contract, that is the baseline behavior, not evidence that the research procedure improved. The attractive number cannot replace the promised metric after the run.',
    outputs:[['Metric audit','Recomputes accuracy, both recalls, and balanced accuracy from the same prediction rows.'],['PROMOTION.md','Uses the declared objective and rejects the unsupported metric-switch claim.'],['Rollback record','Restores the prior active version if the fixture replaced it, while retaining the rejected candidate.']],
    recovery:'If one class disappears from the prediction/target join, repair the diagnostic join before interpreting recall. Do not silently drop those rows. If no active version was actually changed, record a rejection without inventing a rollback event. Choosing accuracy for a genuinely new task requires a new stated objective and tradeoff.',
    hint:'Inspect the class the model never recognizes. Overall accuracy can conceal that failure; balanced accuracy gives each class recall equal weight.'
  },
  '09.01': {
    outputs:[['COMPONENTS.md','Separates the host model, task model, research skill, improver, and external evaluator, with writable surfaces.'],['Three classified edits','Explain a model setting, task-skill revision, and improver-rule revision.'],['Boundary counterexample','Contrasts legitimate internal selection changes with an invalid post-result change to the external metric.']],
    recovery:'If the same agent performs several roles, name that shared authority rather than drawing an imaginary independent evaluator. If every promotion rule is marked immutable, distinguish the candidate improver’s internal rule from the external protocol that judges it. Recursion needs a changed improvement procedure to govern later work, not merely another nested loop.',
    hint:'Ask two questions for each rule: whose decision does it govern, and what unchanged evidence will judge the consequence of changing it?'
  },
  '09.02': {
    example:'In the [recorded bike run](../../evidence/2026-09-20/two-generations/README.md), one unchanged improver rejected a tree in generation 1 and accepted weather features in generation 2. The retained selection MAE went from 109.81 to 109.81 to 99.18. The improver’s file and hash stayed the same. Two generations, including a useful task change, therefore did not establish a revised improver.',
    outputs:[['Fixed improver identity','Shows the same file and hash governing both rounds.'],['Two generation records','Retain parent, proposal, checks, decision, cost, and resulting active skill.'],['Baseline account','Reports retained quality without equating two iterations with recursive procedure revision.']],
    recovery:'If a rejected child becomes the next parent anyway, inspect and correct the active-version pointer while preserving the erroneous trace. If the improver was edited between rounds, this is no longer the fixed baseline. Keep the four-fit ceiling across both generations; a fresh folder does not reset the experiment’s total budget.',
    hint:'Count versions of the improver separately from versions of the task skill. Multiple children do not imply multiple improvement procedures.'
  },
  '09.03': {
    example:'Improver v0 tests only the case that motivated a skill edit. A proposed v1 requires one contrasting case before promotion. On a fixture where the edit helps the first case but harms the second, v1 should make a different retention decision. That verifies the changed rule’s behavior; it does not yet show better future research at matched cost.',
    outputs:[['Improver failure diagnosis','Links one procedural weakness to the lineage that exposed it.'],['IMPROVER-v0.md and IMPROVER-v1.md','Preserve parent, one changed instruction, expected benefit, overhead, and falsifying case.'],['Two fixture decisions','Show favorable and regressing cases under the unchanged external evaluation contract.']],
    recovery:'If the child only says “be more careful,” replace the vague aspiration with an observable action or decision rule. If it consumes more evaluation calls, record that cost rather than treating checks as free. Do not change the external final cases or metric to make the child’s internal rule look successful.',
    hint:'An inspectable revision predicts a decision difference on a named case. A plausible explanation alone does not supply that difference.'
  },
  '09.04': {
    outputs:[['Active improver and ancestry record','Identifies v1 and its parent before the new round.'],['New task-skill proposal and checks','Show an action required by the revised instruction.'],['Inheritance report','Connects identity to executed behavior and distinguishes a measured v0 comparison from an unexecuted counterfactual.']],
    recovery:'If the record has a v1 hash but no contrasting-case check, investigate whether the file was actually followed. Copying an instruction is not evidence of compliance. If the v0 alternative was only described, label it as predicted behavior. Preserve context limits when the same author or chat supplies both rounds.',
    hint:'Find a chain with three links: changed rule, later action, and recorded outcome. A version label supplies only the first link.'
  },
  '09.05': {
    outputs:[['Matched-comparison protocol','Freezes two cases, both improvers, identical starting task skills, two fits per arm/case, and the external metric.'],['Eight fit and decision records','Include attempted and rejected revisions and all available costs.'],['Retained-outcome comparison','Judges the artifact each improver actually retained, with narrow claims about the two cases.']],
    recovery:'If one improver is judged by its best discarded candidate and the other by its retained candidate, recompute the comparison consistently. If agent costs are unknown, do not claim equal total resources. If both arms have identical outcomes, inspect whether their changed rule encountered a case where it could matter; a null result remains valid evidence.',
    hint:'Judge each improver by the consequences of its decisions. Identical candidate scores can still lead to different retained systems.'
  },
  '09.06': {
    example:'If generation 1 accepts improver v1, generation 2 must show v1 governing later improvement work. A rejected v2 must leave v1 active. The [actual bike run](../../evidence/2026-09-20/two-generations/README.md) illustrates the other possibility: both improver proposals were rejected, so v0 remained active even though the task score improved. Its saved proposals, hashes, and generation numbers did not establish successful improver replacement. Keep that negative result instead of adjusting the rule to force an upgrade.',
    outputs:[['Two-generation protocol and lineage','Track both task-skill and improver parents, proposed children, external checks, and the eight-fit maximum.'],['Executed inheritance traces','Show the active improver affecting later improvement work, including rejection paths.'],['Checkpoint and quality/cost report','Preserve active pointers, consumed budget, improvements or regressions, and stop reason.']],
    recovery:'If resumption starts from the newest file rather than the accepted active version, reconcile the checkpoint and promotion record before running. Keep rejected improver children available but inactive. If a generation has no accepted revision, report that outcome instead of relaxing the rule to force a rising curve. Inspect total fits across both generations.',
    hint:'Separate proposed versions, accepted versions, and executed active versions. A recursive lineage needs behavioral inheritance, not just increasing version numbers.'
  },
  '09.07': {
    example:'A run shows improver v1 inherited by later work, but it consumes twice the measured time and retains a worse solver. The evidence can support a structural recursion demonstration while rejecting a benefit claim for that comparison. “Recursive” describes the feedback path; it is not a synonym for successful or accelerating.',
    outputs:[['Claim-to-evidence table','Classifies structure, effectiveness, efficiency, transfer, and acceleration separately.'],['Three case explanations','Use actual artifacts where available and label unexecuted cases.'],['Claim audit','States the strongest supported conclusion and the specific missing evidence for stronger ones.']],
    recovery:'If an answer uses only words such as autonomous or emergent, return to the changed object and observed action. If a case was not executed, keep it as an analysis exercise. Do not manufacture a learner answer or mark a teach-back as passed because an author supplied an answer key.',
    hint:'For each adjective in the claim, ask which artifact could make it false. If there is no discriminating observation, narrow the claim.'
  },
};
