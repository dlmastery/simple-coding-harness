// Individually authored teaching support. Presence does not prove learner validation.
export const guidance = {
  '00.01': {
    example:'Consider an illustrative hour with 3 casual rentals and 13 registered rentals. The total is 16. Adding those two observed counts gives the answer exactly, but the counts are not available before those rentals occur. The useful question is what you could have predicted from permitted information. Now change the request from describing a recorded hour to planning tomorrow: even the weather input needs a different source.',
    outputs:[['TASK.md','States one row, the target and unit, when inputs are available, excluded outcome fields, the metric, and the partition rule.'],['Eight-row display','Shows source rows that support the field explanations. This is data inspection, not a model result.']],
    recovery:'If the agent treats casual or registered as ordinary inputs, return to one row and add the counts. Correct the brief before fitting anything. If it calls observed weather a forecast, ask when that weather value would have been known. A missing forecast source is a task-design gap, not a reason to invent forecast accuracy.',
    hint:'Place yourself just before the prediction is needed. Which values could you actually know then? A column can be present in a historical table and still be unavailable at that moment.'
  },
  '00.02': {
    example:'A text-only agent can explain MAE and draft TASK.md. It cannot produce evidence that a local model ran. An agent with file access may save that brief but still lack a working Python environment. Ask each capability to produce its own small observable result: a read file, an executed command, an imported package, or an opened plot.',
    outputs:[['CAPABILITIES.md','Names the actual Python and package versions, executed checks, and any missing capability.'],['DATA-REPORT.md','Reports 17,379 source rows and the fixed training, selection, and final roles.'],['sample.csv and data-overview.png','Preserve inspected rows and a readable chart from the pinned data.']],
    recovery:'If package installation fails, save the command error and environment path. Have the agent repair that project environment and repeat only the failed capability check. If the data checksum differs, inspect which file was opened; do not edit the expected checksum to accept another dataset. If a chart exists but cannot be viewed, report that display gap separately from plot generation.',
    hint:'Separate “the agent knows how” from “the agent executed it here.” Match each capability claim to a file or command result that could disprove it.'
  },
  '00.03': {
    outputs:[['trial-001/PROPOSAL.md and RESULT.md','Identify the one constant recipe and its measured selection MAE.'],['trial-001/predictions.csv','Contains one prediction per selection row. The predicted value is constant.'],['BASELINE-NOTE.md','Shows three absolute errors and explains why their mean need not equal the full-partition MAE.'],['trials.csv','Contains one completed fit; further candidate search has not started.']],
    recovery:'If predictions vary by hour, inspect the recorded model: this lab requires the constant baseline. If your score differs, first compare source identity, partition rows, runtime, and the saved recipe. Recompute from predictions before fitting again. A second fit is not automatically allowed inside this one-fit experiment; preserve the first attempt and diagnose it.',
    hint:'The baseline learns one number from training. Check where that number comes from, then follow one selection row through subtraction, absolute value, and averaging.'
  },
  '00.04': {
    example:'For illustrative true counts 10, 20, and 30, predicting 20 each time gives absolute errors 10, 0, and 10. Their mean is 6.67. A report claiming MAE 1 is contradicted by those rows. Yet a report claiming 6.67 still needs a second question: were these the correct selection rows? Arithmetic and the meaning of the measurement are separate checks.',
    outputs:[['EVIDENCE.md','Connects the declared candidate and partition to prediction rows and a recomputed MAE.'],['Labelled altered report','Preserves the deliberate false summary separately from the original.'],['Checker results','Show the valid report passing and the false summary failing, with exit status and reason.']],
    recovery:'If both reports pass, inspect whether the checker actually reads the predictions and compares the reported value. If both fail, first check paths and candidate identity on the unchanged original. Do not change the correct predictions to make the deliberately wrong summary pass.',
    hint:'Ask which fact each file can establish. A metric number has no row identities; a prediction table does not by itself explain which partition the rows belong to.'
  },
  '01.01': {
    example:'“Fit a baseline” needs more than a table. It also needs the target, allowed columns, and training rows. Its output is a fitted recipe and predictions. The later checker consumes those predictions and the expected selection-row identities. Writing these input/output pairs reveals why a missing split decision cannot be repaired by a confident final paragraph.',
    outputs:[['PROCESS.md','Contains frame, inspect, split, fit, and check, each with its input, output, and completion condition.'],['Gap review','Traces the existing baseline back to the decisions that make its score interpretable. No new fit is needed.']],
    recovery:'If a step says only “improve quality,” ask what action runs and what evidence marks it complete. If fitting appears before the target or partitions are defined, repair the order on paper. If a step depends on something remembered only from chat, add its source file to the process.',
    hint:'Try to execute the process with the conversation hidden. At each step, name the specific input you would need and the output the next step expects.'
  },
  '01.02': {
    example:'Two runs can produce byte-identical predictions while taking different wall-clock times. The recipe is repeatable; the operating system did not schedule both commands identically. Conversely, matching rounded MAE values can hide different predictions. Compare rows and settings before deciding what repeated.',
    outputs:[['TRACE.md','Records all five process actions, their inputs and outputs, exit status, and elapsed time.'],['New baseline artifacts','Belong to this clean workspace; they are not copied predictions presented as a new fit.'],['REPEATABILITY.md','Compares recipe, source, row identities, predictions, score, and runtime with the earlier run.']],
    recovery:'If a report is missing, check the ledger and prediction file before retraining. If predictions differ, compare versions, feature groups, and split identities. Preserve the difference and identify its cause; replacing the new output with the old one would erase the observation this lab needs.',
    hint:'Separate the intended recipe, the events in this run, and the result. Which of those should remain the same, and which can vary without changing the prediction?' 
  },
  '01.03': {
    example:'A usable instruction says: read the task, verify the pinned data, fit the training-median baseline once, save predictions, recompute MAE, then stop. A tool supplies the fitting operation. The host agent chooses the tool call by following the skill. The skill file contains neither the language model nor a technical barrier that prevents the agent from ignoring it.',
    outputs:[['Learner-owned baseline skill','Contains its trigger, required inputs, ordered actions, one-fit limit, evidence, and refusal conditions.'],['Instruction-to-action trace','Connects specific skill instructions to actual operations in the new run.'],['Checked baseline artifacts','Demonstrate that the saved procedure was followed, rather than merely written.']],
    recovery:'If the skill grows into a copy of the whole chat, keep the procedure and move run-specific observations into the trace. If it says “use the best data,” name the permitted data and prediction-time rule. If execution needs an unstated file, add that dependency before claiming the skill is reusable.',
    hint:'Point to three different things: the written instruction, the operation that implements it, and the evidence that checks its output. Do not treat them as interchangeable.'
  },
  '01.04': {
    example:'Suppose a prediction row has a plausible error but refers to source row 12, which belongs to training. The arithmetic can be correct and the selection claim still invalid. A checker with expected row identities rejects that substitution. A checker given only “MAE 159.95” cannot detect it.',
    outputs:[['Generated checker','Reads expected row identities and source targets as well as predictions and the claimed metric.'],['CHECK-REPORT.md','States the valid verdict, substituted-row refusal, exit statuses, and the checker’s access limits.'],['Unchanged original and altered copy','Make it possible to inspect the exact substitution that caused the failure.']],
    recovery:'If the altered row passes, check that the tool compares the full identity set and detects duplicates, rather than only counting rows. If a valid file fails, inspect identity types, ordering requirements, and source version before relaxing a rule. A separate calculation is useful even when the same agent can read both sides; label that boundary accurately.',
    hint:'A candidate, a row set, and a number must refer to the same experiment. Ask what substitution could leave the number plausible while changing the scientific question.'
  },
  '01.05': {
    example:'A new session reading “repeat our successful run” lacks the decisions hidden in “our.” A handoff that names TASK.md, the skill version, pinned data, setup, workspace, and budget can recover them. Supplying the desired score would encourage imitation of the answer; supply the procedure and let the new execution determine its score.',
    outputs:[['HANDOFF.md','Names every required file, the exact skill version, setup, workspace rule, and one-fit limit.'],['Context-boundary note','States whether a genuinely new agent session was used. A new Python process alone does not count.'],['New run and comparison','Show that the retained procedure was read and executed, then compare its predictions with the earlier recipe.']],
    recovery:'If the new session asks about an unstated scientific choice, add that choice to the handoff and retain the gap as a finding. If the host cannot provide another session, perform a labelled same-context check and leave fresh-session reuse unverified. Do not simulate forgetting and call it isolation.',
    hint:'Imagine handing the folder to someone who has never read this chat. What must they know to run the experiment without being told what answer to print?'
  },
  '02.01': {
    example:'A constant predictor gives the same answer at 3 a.m. and 5 p.m. A model with calendar categories can assign different contributions to those hours. In the saved author run, replacing the constant model with a calendar linear model changed selection MAE from 159.95 to 109.81. Both used the same calendar input group; the comparison isolates a model change rather than adding weather at the same time.',
    outputs:[['Hypothesis or proposal','Links the observed hourly error pattern to the model-family change before fitting the alternative.'],['Two candidate directories','Retain constant/calendar and linear/calendar, with the same seed and scientific contract.'],['COMPARISON.md and hourly error reports','Show the aggregate comparison and whether particular hours still have large errors.']],
    recovery:'If both model family and feature group changed, keep that run but do not interpret it as the specified controlled comparison. If the linear candidate loses, check execution and then retain the losing result; a plausible diagnosis does not guarantee a gain. Never inspect final scores to rescue the choice.',
    hint:'Name the one changed factor and each factor held fixed. Then find one observation that would make you doubt the proposed explanation.'
  },
  '02.02': {
    example:'Suppose three illustrative candidates have MAE 160, 110, and 125. After the third fit, the current candidate has error 125, but the retained best still has error 110. The loop stops because it spent three attempts. Stopping and choosing the retained output are different decisions.',
    outputs:[['LOOP.md','Declares three attempts, allowed recipes, lower-MAE retention, tie handling, and stop conditions.'],['State after each attempt','Shows both the current candidate and retained best, plus attempts used and remaining.'],['trials.csv and COMPARISON.md','Preserve all three results and the choice supported by the declared rule.']],
    recovery:'If the latest candidate replaces a better earlier result, inspect the retention condition. If the comparison shows the wrong attempt limit, check the frozen contract and the first run’s budget argument. Do not increase the contract limit after results arrive. Failed admitted attempts still consume their slots.',
    hint:'Use two labels on the ledger: “just evaluated” and “best retained so far.” Move each label only when its own rule says to move it.'
  },
  '02.03': {
    outputs:[['FEEDBACK.md','Separates the observed weakness, weather-feature hypothesis, alternative explanation, and predicted outcome.'],['DECISION.md','Names the feedback that changed the next action before that candidate is fitted.'],['Two candidate records','Keep linear/calendar and linear/all under the same model family, seed, split, and metric.']],
    recovery:'If the agent explains the feature choice only after seeing its score, label the explanation retrospective and do not claim it was the decision rule. If error slices do not support a weather-specific diagnosis, record that uncertainty: adding weather remains a testable hypothesis. A poorer candidate is retained as evidence and rejected as the preferred recipe.',
    hint:'Draw three boxes: observation, hypothesis, action. Only the first is already measured. The experiment tests the connection between the other two.'
  },
  '02.04': {
    example:'The proposed sequence linear/calendar → tree/calendar → linear/calendar contains two distinct recipes. A useful controller detects the return to the first recipe before another fit starts. A fourth distinct proposal is a different refusal: it exceeds the two-fit budget. Keeping both reasons shows that duplicate detection and budgeting are separate checks.',
    outputs:[['Generated controller and LOOP.md','Define recipe identity, duplicate handling, the total attempt limit, and stop behavior.'],['Request trace','Records the two admitted recipes, duplicate refusal, and distinct over-budget refusal.'],['Fit ledger','Shows no extra model fit for either refused request. A refusal has a reason, not an invented score.']],
    recovery:'If the duplicate runs again, inspect which fields the fingerprint includes and whether it is checked before fitting. If an over-budget request succeeds after restart, inspect whether the limit and spent attempts were reloaded. To study intentional replication, declare a separate comparison that permits it; do not relabel an accidental repeat after it happens.',
    hint:'Compare recipe identity before comparing scores. A new explanation for an unchanged recipe does not create a new experimental intervention.'
  },
  '02.05': {
    example:'A three-attempt experiment stops after candidate 1. Its checkpoint says one used and two remaining. Opening another session changes neither number. If candidate 2 later starts and is interrupted, that admitted attempt still belongs in the ledger. Candidate 3 must get a new identity; it cannot overwrite candidate 2 and conceal the failure.',
    outputs:[['PROGRESS.md at the stop boundary','Records the completed candidate, contract, spent and remaining attempts, retained result, and next action.'],['Original candidate artifacts','Remain unchanged after resumption.'],['Combined ledger and final state','Show unique identities across sessions and the original three-attempt limit.']],
    recovery:'If a lock exists, inspect the recorded process and whether it is still active before touching it. Preserve an exited process’s interrupted trial and known cost. If the checkpoint disagrees with the durable ledger, reconcile the actual artifacts first. If source or contract changed, keep this experiment intact and use a separate reviewed experiment.',
    hint:'Distinguish the lifetime of the program from the lifetime of the experiment. Which state must survive when the program stops?'
  },
  '02.06': {
    example:'In an illustrative two-fit comparison, blind repetition returns errors 160 and 160. A feedback-guided procedure returns 160 and 110. The second procedure retained a better candidate with the same number of fits, but its proposal and review may have cost more. Another task could reverse the outcome. This tests two fixed search procedures, not a procedure revising its own improver.',
    outputs:[['COMPARISON-PLAN.md','Fixes both starting states, two-fit allowances, permitted changes, retention, and cost reporting before execution.'],['Separate arm workspaces','Retain the intentional baseline repeat in A and the recorded adaptive choice in B.'],['Comparison report','Shows each retained result, all attempted recipes, available costs, and the actual context boundary.']],
    recovery:'If a duplicate controller blocks arm A, inspect the predeclared purpose: this arm intentionally measures fixed repetition. Have the agent implement that explicit replication allowance in a separate arm-specific controller before execution. If one arm gets extra attempts, preserve the outcome but do not claim an equal-budget comparison. Unknown inference cost stays unknown.',
    hint:'The object being compared is how each procedure spends its attempts. Count the failed and repeated attempts too, then separate that count from total research cost.'
  },
  '03.01': {
    example:'The fit action produces predictions.csv. The metric check consumes that file. Drawing fit → check records a dependency, not a preference about page layout. Moving the check earlier leaves it without its required input. Two actions with no shared dependency may be reordered, but only if they also avoid conflicting writes.',
    outputs:[['WORKFLOW.md and diagram source','Name each action and the artifact carried by each dependency.'],['Rendered workflow','Shows readable arrows and labels; the source remains editable.'],['Ordering-check results','Record a valid order and an invalid order that tries to check predictions before they exist.']],
    recovery:'If an arrow has no named input, ask what would prevent its destination from running first. Remove decorative edges that assert no real dependency. If the invalid order passes, inspect whether the checker verifies every predecessor rather than only counting nodes. Keep diagram syntax failures separate from failures of the workflow itself.',
    hint:'Cover the preceding action with your hand. What input would the next action lose? That missing input is the reason for a dependency arrow.'
  },
  '03.02': {
    example:'A sample containing cnt can pass the required-target check. A sample missing cnt is invalid. A missing check report is unknown: it supplies no verdict at all. Both invalid and unknown should stop this route, but for different reasons. Recording those reasons tells the next step whether to repair data or obtain missing evidence.',
    outputs:[['WORKFLOW.md','Defines valid, invalid, and unknown conditions and their destinations.'],['Three preserved fixtures','Include the valid sample, missing-target copy, and absent-evidence case.'],['ROUTES.md','Shows each input, observed condition, chosen action, and exit status; invalid and unknown never reach fitting.']],
    recovery:'If missing evidence reaches the success branch, inspect the router’s default case. Make unknown explicit instead of treating every non-failure value as a pass. If a fixture changed pinned source data, restore the source from its recorded version and keep the mutated fixture in the learner workspace.',
    hint:'“The check found no error” and “the check never returned a result” are different statements. Follow each through the branch conditions.'
  },
  '03.03': {
    outputs:[['Data and resource check records','Each names candidate identity, contract version, outcome, and whether the input is a teaching fixture.'],['Join implementation','Requires both matching passes before continuing.'],['JOIN-REPORT.md','Preserves complete, missing, and mismatched cases and states whether execution was sequential or concurrent.']],
    recovery:'If a mismatched pair passes, compare the identities before combining the booleans. If one result never arrives, stop at the declared wait limit and report incomplete evidence. An invented resource-pass fixture can test join logic, but must not be presented as a measurement of available RAM, cost, or cluster capacity.',
    hint:'Write the candidate name beside every pass. You need two passes for the same object under the same contract, not merely two successful checks somewhere.'
  },
  '03.04': {
    example:'An illustrative report lacks a required candidate ID. Repair 1 adds that ID, so rechecking succeeds. In a second fixture, both repairs change only the title. The ID remains missing; the graph exits with failure after repair 2. Both runs terminate correctly, although only one repairs the artifact.',
    outputs:[['Graph and state rules','Show check → repair → recheck and both terminal exits, with a two-repair allowance.'],['Successful repair trace','Shows the missing field becoming present and the unchanged validator accepting it.'],['Exhausted repair trace','Shows two ineffective edits and a terminal failure without another hidden attempt.']],
    recovery:'If the repair counter returns to zero on the back edge, store it in the experiment state rather than inside one node invocation. If a repair succeeds by deleting the required-field rule, reject that result: it changed the evaluator instead of fixing the artifact. Keep ineffective edits so the failure can be explained.',
    hint:'Count repairs separately from checks. The first check discovers the problem; later checks decide whether a repair worked under the same rule.'
  },
  '03.05': {
    example:'A report writer crashes after predictions are saved and checked. Rewriting the report needs those existing outputs, so another fit adds no necessary evidence. Change the split instead, and the fitted recipe’s training membership and evaluation membership change. The old downstream results cannot simply be relabelled as belonging to the new split.',
    outputs:[['Injected failure record','Identifies the failed report operation while preserving the existing prediction identity.'],['Recovery trace','Names the reused inputs and repaired report; the fit count does not increase.'],['Invalidation plan','Lists which descendants become stale after a changed split or substituted prediction file.']],
    recovery:'If the recovery starts training automatically, inspect whether the failed node actually invalidated model inputs. If it reuses an old score after predictions changed, compare the recorded input identities. Do not overwrite stale results: retain them with their original input versions and create fresh descendants where required.',
    hint:'Start at the changed artifact and walk forward through dependency arrows. Work outside those descendants may remain valid if its own inputs and checks still match.'
  },
  '03.06': {
    example:'The plan permits fit → check → report. The data-flow table says the checker reads candidate A’s predictions. A failed trace ends just after fitting. You can claim a model ran, but cannot claim the check passed or that its report exists. Adding a “verified” box to the diagram does not add a missing execution event.',
    outputs:[['VIEWS.md','Contains the control graph, artifact-flow table, and time-ordered events for one real run.'],['Failed-trace audit','Identifies an allowed action that did not execute and the output that cannot be claimed.']],
    recovery:'If all three views are the same unlabeled picture, ask each to answer its own question: what may run, what data moves, and what did run? If an event lacks its output, inspect the underlying command before calling it complete. Mark missing trace evidence as missing rather than reconstructing a successful event from the plan.',
    hint:'A route map does not show which road a particular trip took. The same distinction separates the workflow plan from an execution trace.'
  },
  '04.01': {
    outputs:[['VOCABULARY.md','Classifies concrete objects and distinguishes dataset, column, target role, partition, recipe, fitted model, metric, and measurement.'],['Three rewritten claims','Name whether a result concerns task-model error, a research-skill edit, or changed language-model weights.']],
    recovery:'If “model” refers to several things, name each explicitly: fitted task model, research agent, or language model. If the supplied runner did not save fitted weights, do not invent a model file; identify the recipe, the fitting event, and the retained predictions. A numeric score needs candidate, data role, metric, and unit before it is interpretable.',
    hint:'Distinguish the instruction “calculate MAE” from the resulting number, and the recipe “fit this estimator” from the parameters learned in one execution.'
  },
  '04.02': {
    example:'“Scaler fit on train” is a statement about the meaning of a transformation. “Fit scaler before transform selection rows” is a dependency between actions. They cooperate: one says which data is permitted, the other says what must happen first. Neither statement alone supplies the other.',
    outputs:[['DOMAIN.md','Contains the Subject, Relation, Object facts for the declared bike experiment.'],['DOMAIN-CHECK.md','Shows the executed verdict and names the supplied checker’s limited rules.'],['Plain-language explanations','Translate each fact into a sentence and distinguish it from an execution dependency.']],
    recovery:'If the checker reports an unknown relation, compare the intended meaning with its documented relation vocabulary; define and test any extension separately. If the table passes while an important fact is absent, add the missing fact and review the coverage. A pass is not proof that the table describes every scientific constraint.',
    hint:'Read each row as a sentence. Does it describe what an object means or which action should execute next? Those are different kinds of relation.'
  },
  '04.03': {
    outputs:[['RULES.md','States the target-derived-input, train-only-transform, and selection-versus-final invariants.'],['Six fact tables','Give one isolated valid case and one isolated violation for each rule.'],['RULE-TESTS.md','Pairs expected and actual verdicts, preserving all inputs and outputs.']],
    recovery:'If a negative case passes, check that the table contains the relationship needed to trigger the rule. A renamed leaked feature still needs its derivation fact. If a case triggers several rules at once, split it into smaller fixtures so each failure has a clear cause. New checks such as measurement units need an explicit extension; the supplied three-rule checker does not already enforce them.',
    hint:'A rule earns trust by separating a valid case from a closely related invalid one. Change just the fact that should cross that boundary.'
  },
  '04.04': {
    example:'“Model uses feature total_users” can look harmless until another fact says “total_users is derived from target.” The contradiction comes from their relationship. Rename the feature to f7 in both facts and the same violation remains. A name does not remove the information carried by a column.',
    outputs:[['Original teaching DOMAIN.md','Contains the well-formed leaked-input, final-fitted-scaler, and final-selection violations.'],['Failure report','Names all three semantic failures.'],['Corrected facts and recheck','Pass the supplied rules while preserving the original failed case and explaining which computations would need rerunning.']],
    recovery:'If renaming makes the leakage warning disappear, check whether the derivation fact was renamed consistently or accidentally deleted. If the documentation is corrected after an actual leaked fit, keep that score marked invalid for the intended comparison. Repairing the facts does not repair the training history.',
    hint:'Follow where the feature’s information comes from. The relevant fact is its relationship to the target, not whether its name sounds suspicious.'
  },
  '04.05': {
    example:'In an illustrative forecasting record, the prediction is issued at 09:00 for tomorrow at noon. Tomorrow’s observed noon temperature arrives after the issue time and is unavailable to that prediction. A weather forecast issued before 09:00 might be permitted, but the pinned bike table does not contain that archive. The availability test can use labelled synthetic timestamps; it cannot create the missing real forecast data.',
    outputs:[['Vocabulary versions 1 and 2','Preserve the retrospective meaning and the new forecast-origin definition separately.'],['CHANGE.md and IMPACT.md','Trace affected sources, features, recipes, split assumptions, and evidence that cannot be reused as a forecast result.'],['Availability test','Rejects an input released after the prediction origin and labels any constructed timestamp fixtures as synthetic.']],
    recovery:'If a new forecast score appears without a forecast source, stop and inspect which data was actually used. Keep the activity as an impact analysis until the required historical inputs exist. If timestamps are ambiguous, define their time zone and release-time meaning before testing availability. Do not rename observed weather and treat it as a forecast.',
    hint:'Keep two times separate: when the event occurs and when the input becomes available. The second decides whether the feature belongs in a prediction made at a given origin.'
  },
};
