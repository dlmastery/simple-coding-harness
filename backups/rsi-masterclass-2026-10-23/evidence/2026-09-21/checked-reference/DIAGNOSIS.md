# Diagnosis from traces

The parent read both inputs but checked only Target and Metric and emitted complete. The valid reference checked the remaining required field and emitted missing Split. The shortcut reached that same answer without reads or checks and was rejected. Reversing the two input reads remained valid. The missing check is the actionable defect; the read-order difference is not.
