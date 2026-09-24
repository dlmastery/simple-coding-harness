# Matched improver comparison

Recorded before generating or fitting the comparison cases on 20 September 2026. This is the bounded comparison stage of the [clean journey](CLEAN-JOURNEY-PROTOCOL.md).

## Question

Does changing a task-skill promotion rule change the descendant retained from a matched starting point? The weak teaching control uses training performance. The revised rule requires better held-out selection performance. Neither rule changes the external metric, data partitions, or final evaluation.

The author prepares both procedures. A labelled diagnostic fixture, not an ML measurement, motivates the revision: parent training MAE 12 and selection MAE 15; child training MAE 0 and selection MAE 24. A second fixture has selection MAE 10. These fixtures check the intended branches before new data is generated. This constructed weak control is not a competitive research baseline.

## Three objects

- The solver is the generated scikit-learn training pipeline.
- The task skill is a Markdown procedure that selects the model family, trains on training rows, and saves predictions. Parent: scaled ridge for regression or scaled logistic regression for classification. Proposed child: an unpruned decision tree with seed 17.
- The improver proposes that fixed child and decides whether to retain its task skill. Version 0 uses training score. Version 1 uses selection score. The later comparison reads each saved version and executes its specified decision.

This tests an inherited change to the acceptance stage of an improvement procedure. It does not test autonomous proposal quality, self-authored procedures, language-model learning, or a general Markdown interpreter. The driver implements the two explicit rules and model choices written in the supplied files.

## Prespecified cases and resources

Generate 1,000 rows per case with scikit-learn. Regression: `make_regression`, 12 inputs, 8 informative inputs, noise 30, seed 99173. Classification: `make_moons`, noise 0.25, seed 99179. Save all rows and identities. Partition each into 60% training, 20% selection, and 20% final with seeds 421 and 422; stratify both classification splits. These are synthetic teaching cases, not new UCI measurements.

Each improver gets both cases from the same parent skill, the same fixed child proposal, and two model fits per case. Eight fits total. The case order is regression, then classification. Alternate the arm order by case to reduce systematic order effects on timing. No tuning, retries, additional seeds, or replacement of a losing case. A fit failure is retained and stops the stage for diagnosis.

Use ridge alpha 10 after training-only standardization, logistic regression with balanced class weights and 1,000 maximum iterations after training-only standardization, and unpruned decision trees. Measure regression by MAE, lower is better; classification by balanced accuracy, higher is better. Promotion requires strict improvement on the partition named by the procedure. Ties retain the parent. Report training and selection values for both candidates in both arms.

Save and hash all promotion decisions before any final predictions or scores. Then evaluate the already fitted parent and retained descendant on final rows. Final evaluation performs no additional fitting. Retain predictions sufficient to recompute every reported value. Do not choose, revise, or rerun an improver after observing final outcomes.

## Evidence boundary

Use one authoring-agent context and separate Python processes for fits. A fresh Python process is not a fresh coding-agent context. All files are visible to the host; the final partition is a cooperative workflow boundary. Log child commands, exit status, wall time, fit time, rejected proposals, file identities, and the exact decision rule read. Hosted-agent inference and authoring costs are unavailable; do not claim equal total cost or cost superiority.

Only two deliberately chosen task families and one split per family are tested. Describe results per task; do not average incompatible metrics. A favorable result supports the changed decision in these cases. It does not establish general improver superiority, sustained recursive improvement, acceleration, independent replication, or learning effectiveness with students.
