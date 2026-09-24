# Generated workflow

Read the task and source data card → inspect data and partition roles → validate allowed inputs → fit one baseline → check predicted row identities and recompute the metric → consider the declared candidate if budget remains → compare checked candidates → report and stop. Invalid task arguments fail at entry. Invalid feature requests fail before model fitting and consume an admitted attempt. Duplicate and exhausted-budget requests do not add a fit. Final evaluation is a separate explicit action.
