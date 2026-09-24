# Discovery, replay, and online confirmation

Author protocol for 10.07–10.09, declared before execution on 21 September 2026. Use a new sibling workspace. Retain all commands, source versions, predictions, decisions, failed attempts, and cost records. Stop on an unexpected result or changed frozen input. No learner or isolated agent context participates.

## Discovery: three fits

Use the unchanged bike tool, seed 17, all permitted inputs, and one experiment with attempt limit three. Root R denotes the unscored initial workspace. Fit A: training-median baseline. Pause to inspect it and save an actor branch decision. Then fit B: linear/all, and C: tree/all, both conceptually derived from A's baseline observation. This is recipe ancestry, not a saved-workspace fork implementing the paper's node eligibility. The author has prior bike-result exposure; no blind discovery claim.

Save the planned table with blank scores before A. Fill it only from actual trial records. Check all three outcomes. Add D under B as a proposed forest recipe with no fit or measured score. Render the measured tree and the proposed branch distinctly. No final evaluation.

## Replay: no fits

Freeze the tree. Two fixed order policies spend at most two recorded attempt units: P0 visits A then B, P1 visits A then C. The replay program enforces recorded parent access and only reports a score after revealing its node. It never imports a training module or launches a process. Known cumulative fit seconds and actual replay computation time are separate from the two-unit attempt allowance. Author proposal and inference costs are unknown.

Select the policy with lower best visited MAE; ties retain P0. Query one absent branch E under B and retain unknown. For the additional coverage activity, remove the selected policy's second node in a separate tree copy, rerun both same policies, and report the changed support/ranking without adding any environment evidence. Do not replace the original tree or selection result. These fixed recipe orders are a simpler teaching interface than Dream-RSI's root/leaf batch transitions and objective.

## Online: four fits

Before any online fitting, freeze P0, P1, and the original replay selection. Generate seed 61009: 600 IID rows, six independent standard-normal inputs, target 100 + 25*x0 - 18*x1 + 12*x2 + Gaussian noise with standard deviation 3. Roles are 360 training, 120 selection, and 120 evaluation. This is a constructed continuous regression task, different from bike demand. The author knows its generating formula; evaluation labels are host-readable. The rows and outcomes are new, not a blind task or a generalization benchmark.

Give each policy two fits on identical rows: A is DummyRegressor(strategy=median); B is StandardScaler then Ridge(alpha=10); C is DecisionTreeRegressor(max_depth=8, min_samples_leaf=15, random_state=17). Policies use the same recipe names, fixed order, and lower-selection-MAE retention rule as replay. Both recipes use all six inputs. Save the policy, source, and data hashes before fits. Run each fit in a subprocess with a 60-second timeout and a started/finished ledger. Failed attempts count. No third fit per arm.

Freeze both retained candidate choices before evaluation; load only trusted locally generated models after checking hashes, with no refits. Check row identities, target values, and MAE from saved predictions. Include the three discovery fits, replay computations, and four online fits in the cost summary. Do not treat replayed outcomes as actual saved expenditure or omit preparation. No parallel-worker or inference-efficiency claim.

After observing results, the actor may write one unexecuted revised-policy proposal. Explain why a new confirmation set and budget would be needed. Do not modify either tested policy or run another fit. Archive and verify all raw files.
