# Online discovery and policy evolution

Declared before the first online discovery fit, 22 September 2026. This follows the two development pilots. It is a controlled laptop adaptation, not reproduction of a paper's benchmark or evidence of general autonomous RSI.

## Initial execution

Create two new development tasks: classification seed 1101 and regression seed 1102. Each has 1,200 training and 800 selection rows, ten numeric features and a noisy target. Feature scaling and latent coefficients vary by task seed. The generator cycles among linear, interaction and curved signals, so a rule that always expands interactions is not assumed to win. These are fresh task instances of a declared synthetic family, not unseen scientific domains.

The initial fixed exploration policy opens three independent starts, then refines the currently shallowest branch. This is a broad, round-robin control. Retain an additional greedy control for later comparisons. A frozen deterministic pipeline proposer supplies drafts and local changes; the coding agent will revise the exploration-policy code. Replacing the paper's LLM discovery agent with this small proposer is an explicit simplification. The full actor/verifier and researcher-rewriting lessons still require their distinct mechanisms.

Each initial rollout permits 12 attempts and 120 charged worker-process seconds, with at most 60 seconds per subprocess and one numerical-library thread. An attempt launched with less remaining time receives that shorter timeout. Failed and timed-out attempts remain charged. Policy, proposal and snapshot overhead are measured separately; agent inference costs remain unknown. These worker limits are not a claim of equal total research cost.

Every child starts from an actual copy of its selected parent's saved workspace. Record the inherited file hashes, generated code, changed parameters, predictions, score, source identities, timings and a terminal outcome. The proposer reads the inherited candidate source before editing it. The initial workspace has no fitted score. A child may worsen its parent's score; retain both, and select the best observed valid candidate at the end.

Use the same root-or-observed-leaf decision interface online and in replay. Recorded trees are never reconstructed from the earlier flat-grid pilot. Policy views omit unrevealed outcomes and task seed. The local files remain available to the maintainer, so this is a cooperative interface boundary rather than secure isolation.

## Policy development after the first trees

Freeze the accumulated trees. Replay the incumbent and at most three agent-written revisions for at most eight decisions on each tree. A revision must not query unrevealed scores or use future task IDs. Preserve every version and its decision trace. Unknown continuations stay unknown. Do not promote a revision with unknown requests or no valid observed candidate.

For this teaching experiment, minimize mean normalized selection loss plus 0.001 times represented worker-process seconds. Classification loss is twice the balanced error; regression loss is MAE divided by the training-median predictor's selection MAE. This declared replay objective includes an explicit quality/cost tradeoff; report its two components separately. It is not a final predictive-quality metric or a total-cost measure.

The next policy is the lowest-utility valid candidate, including the incumbent; exact ties retain the incumbent. Freeze it before deploying on the next pair of development tasks (1103 classification, 1104 regression), then add the new trees and repeat once on 1105/1106. At most three online generations and 72 online attempts in this initial method-development allocation. Additional matched controls and evaluation have separate allocations declared before execution.

## Later evaluation boundary

Reserve procedure-selection task seeds 2101–2104 and final task seeds 8101–8116, alternating classification and regression. Do not generate these pools during initial policy development. Declare their execution resources, baseline policies, paired analysis and freeze records before use. Synthetic instance transfer and real-data transfer are separate questions. The already exposed public datasets remain development/negative controls; they do not become fresh final tasks by relabelling.

Later comparisons must distinguish final predictive quality, number of actually executed fits, time, failures, proposal/replay overhead and uncertainty. The seven original method comparisons, updater inheritance, full lesson integration and presentation remain required. This protocol does not shrink that scope to a replay demonstration.
