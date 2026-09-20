# ScienceBuddy teaching activities on a laptop

Declared before execution on 20 September 2026. Covers labs 10.22–10.26 in a new sibling workspace. This is a classroom adaptation, not a paper reproduction or a real researcher interview. No new ML fits or LLM training occur.

## Inputs and allowed work

Reuse the preserved wine majority and logistic selection predictions in `rsi/evidence/2026-09-20/author-wine/`. Verify source row identities and targets against the pinned wine source and partition. Preserve exact input bytes and hashes. Do not open final predictions or refit a model. Save the classroom request exactly as a labelled synthetic fixture.

Lab 10.22 derives a task and rubric, then checks a complete report and a copy missing minority recall: two report checks. Criteria require the fixed label threshold, complete linked predictions, both class recalls, balanced accuracy, and a limit statement. The conceptual GWAS note uses an explicitly invented association example and an official glossary reference; no biomedical analysis is executed.

Lab 10.23 changes an external reporting skill. A constrained reporter reads the saved parent or child instruction before producing each report. Complete evidence contains both preserved prediction files. Incomplete evidence removes all true-positive-class rows from both files and is labelled as altered. Generate parent and child reports for both fixtures: four report/check pairs. The child must report missing evidence instead of inventing class results. Distinguish a complete task result from an honest refusal. Retain the longer-but-equivalent instruction variant as text only; do not add a fifth report run.

## Numerical update: lab 10.24

Represent four actions with initial logits zero and softmax probabilities 0.25. True synthetic rewards are `[0,0,1,1]`. One case uses those rewards, one uses four equal observed rewards, and one incorrectly changes only action 0's observed reward from 0 to 1. No rollouts are sampled; these four enumerated actions are a numerical teaching group.

For each case calculate the population mean and standard deviation, then `A_i = (r_i - mean)/(std + 1e-8)`. With fixed advantages, define the toy objective `J(theta) = mean_i A_i log softmax(theta)_i`. Take one gradient-ascent step with learning rate 0.4. Check the analytic gradient by central finite differences with step 1e-6, check finite probabilities summing to one, and preserve initial/updated logits and probabilities.

The equal-reward case must have zero advantages and no update. The incorrectly rewarded action can gain probability even though its true reward is zero. Report both this local wrong direction and the total expected true reward; do not assume the latter decreases. Exactly three cases, no tuning or additional training. This objective omits token-level GRPO machinery and must not be called full GRPO.

## Paired-state simulation: lab 10.25

Use exactly four invented values: M0/H0 = 0.40, M0/H1 = 0.70, M1/H0 = 0.80, M1/H1 = 0.60. Read each once, then cache the four table evaluations. Start at M0/H0; select the best harness for M0; apply the declared model-update placeholder to M1; reselect the best harness for M1. Log both version IDs at every transition. The placeholder is not training. No score is an empirical model measurement.

## Source audit and extension planning

For 10.26, inspect the primary paper's selected methods and result definitions. Store three explicitly paper-reported metric rows separately from local and synthetic values. Compute percentage-point changes and relative changes from the published rounded inputs using a small calculation. Preserve the section-title/body cycle-count discrepancy rather than silently rewriting the source.

Read the scale skill and its brief, adapter, and backend-check contracts. Draft one shared larger-training plan for 10.24 and 10.25. Model/checkpoint rights, GPU memory, hardware, scheduler, cost ceiling, and training hyperparameters remain unresolved until checked on the user's actual backend. No GPU job, purchase, or remote submission is authorized by this planning exercise.

## Evidence and limits

Save the protocol, exact driver, all source inputs, six report-check records, three numerical cases, finite-difference errors, four paired values and transition records, arithmetic results, source audit, and planning notes. Refuse to overwrite the workspace. Record command status and wall time. Learner responses remain unattempted; reporter behavior is deterministic under an author-written interpreter, not an independent trial of a language model's response to a skill edit.
