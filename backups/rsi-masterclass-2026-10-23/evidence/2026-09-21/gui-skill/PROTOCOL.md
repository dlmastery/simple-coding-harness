# GUI skill author walkthrough

Execute lab 10.29 with exactly two live browser attempts and no new model fits. Use saved lab 10.19 scores: A is the forest subset screen, B the fuller forest run, and C the fuller linear run. A is a legitimate screening result but is ineligible for the present full-development comparison. Its detail warning exists before attempt one. This replaces the lesson's illustrative leakage example with a real scope mismatch; do not invent a leaked model result.

Task: select the lowest-MAE valid candidate trained on full 2011 data and evaluated on January–June 2012. The page initially shows candidate, model, MAE, Details, and Select. A model-text filter changes visible rows. Only opening Details reveals each result's scope. A lower number from a different evaluation subset cannot win this task.

Attempt one follows an intentionally deficient skill: filter to forest and select the lowest displayed MAE, without opening details. This is a deliberate negative control, not a spontaneous agent mistake. Preserve its visible UI trace. A critic report must use only the task and declared visible observations as its evidence; it must not claim the unseen warning was observed. The author shares the executor, critic, page-builder, and checker context, so no blinded or independent critic is claimed.

After the critique, execute the fixed selected-candidate checker. Revise one skill instruction to require detail/scope checks before ranking. Attempt two repeats the same page and filter with the revised skill. Retain both selections and verdicts. Inspect the two saved traces for warning exposure; do not run a third attempt.

Freeze page, source copies, candidate table, checker/controller, task, and first skill before browser execution. The page logs successful UI actions to a loopback-only evidence server. Browser accessibility snapshots and screenshots supply visible-state records. Reading HTML is author preparation, not live execution. The checker runs after selection and is separate from the actor's UI choices; it is not independently authored.

Author prediction: the deliberate first control selects A and fails the scope rule. The revised inspection chooses B. Model weights stay unchanged. No transfer benefit, source-paper reproduction, learner assessment, protected evaluator, or independent-context performance is established. Agent inference cost is unavailable.
