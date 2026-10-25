# Keep the workflow, change the scientific contract

The historical bike and wine packages share one recorded builder identity. Their fixed task wrappers differ because the briefs differ. The bike task predicts hourly rental counts with MAE and a chronological split. The red-wine task predicts quality at least 7 with balanced accuracy and feature-group partitions.

The two saved wine prediction files both pass the current result checker. Of the 319 selection rows, 278 are below the threshold and 41 meet it. The majority baseline has class recalls 1 and 0, hence balanced accuracy 0.5. Logistic regression has recalls 204/278 = 0.73381295 and 31/41 = 0.75609756, hence balanced accuracy 0.74495526. No new wine fit occurs in this walkthrough.

Recomputing the feature-only grouping finds 1,599 rows, 1,359 distinct input vectors and 240 extra repeated-input rows. Zero identical-input groups cross partitions. This checks exact repeats under wine-v1; it does not establish independence of near-duplicates or remove every possible data dependency. No final outcome statistics are used in the audit.

Shared workflow: inspect, freeze partitions, fit on training rows, check predictions, compare on selection, preserve evidence and stop. Changed components: target transformation, split meaning, estimator family, metric direction and class-specific error analysis. The builder has not improved merely because its output suits a second brief.

ORDINAL-BRIEF.md is a proposed new task, not another execution. Its evaluator cannot reuse the binary target or balanced accuracy unchanged. Old binary predictions remain evidence about their old question.
