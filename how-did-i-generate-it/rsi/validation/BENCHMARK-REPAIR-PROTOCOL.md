# Repair the RSI experiments

Started 22 September 2026. User objective: "fix the issue and run the lessons - do not stop until the goal is done".

## Completion requirements

The original seven comparisons remain in scope: proof, meta-harness gating, Dream-RSI, Recuris, RSIAgent, AIDE2 and MetaSkill. Link their repaired mechanisms to the current course lessons and capstones. Preserve historical failures. Finish the presentation requested in [the presentation brief](PRESENTATION-BRIEF-2026-09-22.md) after the experiment and evidence gates.

1. Establish useful search headroom against sound baseline procedures on development tasks.
2. Implement the complete mechanisms being taught, including actual retained changes and later use. Compare each adaptation with its source and state remaining differences.
3. Run bounded improvement cycles. Keep ancestry, proposals, rejected candidates, replay coverage, observations and resource use.
4. Freeze procedures before separate task-level evaluation. Distinguish unseen task instances from unseen task families and from unseen rows.
5. Report predictive quality, actual cost, failures, variation and meta-optimization overhead separately. Do not combine a predictive tie with an efficiency win.
6. Reconcile lesson instructions, skills, evidence and claims with the actual runs. Verify the revised activities through the published student entry path.
7. Deliver the evidence-grounded PowerPoint, speaker notes and source artifacts; render and inspect it.

These gates are currently incomplete. An illustrative mechanism run does not establish effectiveness. A fixed optimizer selecting model parameters does not establish an improved improver. Positive gains are the desired outcome, but final tasks cannot become a tuning set to manufacture that outcome.

## Development pilot, declared before fitting

Purpose: check whether a laptop-scale search space contains meaningful choices. This is not a final evaluation, autonomous RSI experiment or paper reproduction.

Six development tasks: UCI Bike Sharing hourly demand regression; UCI red wine quality regression; scikit-learn's breast cancer and digits classification datasets; generated Friedman regression; and generated interaction classification. The existing public course data are already exposed. No source is presented as secret. The synthetic tasks are diagnostic controls, not substitutes for real-data transfer.

Bike uses 2011 training and 2012 January-June selection, keeping the existing July-December final rows out of this pilot. Features exclude total-count components and identifiers; observed weather makes this demand estimation with available weather, not an operational forecast. Wine uses the existing feature-group hash split for training and selection, excluding its historical final groups. Each of these existing partitions is capped at 1,200 rows by deterministic sampling without using labels. Other tasks use a fixed 60/40 train/selection split with stratification for classification. Generated datasets have 2,000 rows each. No new final pool is constructed or inspected in this phase.

Search space: six families, eight configurations each (48 pipelines). Families are regularized linear models, RBF support-vector machines, nearest neighbours, random forests, extra trees and histogram gradient boosting. All transformations fit on training rows only. Numeric imputation/scaling and categorical one-hot encoding are inside pipelines. The source code and recipe table are retained before execution.

Maximum allocation: 288 attempted fits, one per task and candidate. Each attempt has a 60-second subprocess timeout and one numerical-library thread. Failed or interrupted attempts remain charged. A failed attempt is never silently retried. All predictions, selection scores, timings and package/source identities are saved. Agent inference cost is unknown and excluded from fit-time comparisons; this limitation prevents total-cost efficiency claims.

Analysis is prespecified: for budgets 4, 8 and 16, compare (a) a fixed diverse order beginning with a sensible configuration from each family and (b) 32 fixed-seed uniform random permutations without replacement against the best selection score among the 48 candidates. This larger search is a development reference, not a true oracle or a held-out result. Any simulation of shorter searches reuses observed scores and is labelled replay, not extra executed fits. Record the gap per task, the variation over search seeds and the fit time of each selected trajectory. Zero and negative findings remain visible.

Regression uses MAE; classification uses balanced accuracy. For cross-task diagnostics only, use regression MAE divided by the training-median predictor's selection MAE, and classification error divided by the training-majority predictor's selection error. Lower normalized loss is better. The normalization never changes within a task. Do not compare raw MAE with classification accuracy.

## Subsequent design decisions

Only development evidence may guide revisions to candidate operators, search policies and task sampling. Archive every pilot revision. Declare task pools, promotion rules, budgets and final evaluation before running the effectiveness comparisons. A public local holdout is a procedural boundary, not secure isolation.

The agent is implementing the benchmark tools; students will use natural-language skills. Headroom is a prerequisite for the later loops, not the new definition of completion.

## Deviation found during the first pilot

After bike fits completed, a review against the existing data card found that the pilot's adapter omitted clipping count predictions at zero. Eighteen of its 48 bike candidates contain negative predictions (1,702 prediction values total). This is an adapter defect, not an additional search finding. The raw execution remains preserved. A separately labelled derived analysis applies the existing count rule to every bike candidate, retains the original fit costs, and recomputes all aggregates without new fitting. Both versions receive independent prediction checks. The correction was not declared before observing the development results and must not be described as such. Final tasks remain untouched.
