# Changed split: plan only

Affected actions: check, fit, report, split. Predictions, metric checks and reports become stale for the changed split. Frame and inspection may be reused only if their own inputs remain unchanged. Old artifacts keep their original meaning. No descendant executes here.
