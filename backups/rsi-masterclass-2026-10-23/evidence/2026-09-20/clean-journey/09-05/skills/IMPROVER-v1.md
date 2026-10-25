# Improver v1

Read the parent task skill. Propose one child that replaces its fixed linear choice with an unpruned decision tree. Preserve the task, inputs, metric, and partitions. Run both task skills once on the same case. Recompute training and selection scores from saved predictions.

Promote the child task skill only if its selection score is strictly better than the parent's selection score.

Retain the parent on a tie. Keep the rejected skill and both fits. Record the inherited version and decision before final evaluation. Stop after these two fits.
