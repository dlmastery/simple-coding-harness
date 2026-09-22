# A new definition changes the experiment

| Item | Required change | What can remain |
|---|---|---|
| Prediction request | Name origin, target time, location and available information | The rental-count target and unit if the operational question retains them |
| Source data | Obtain historical forecasts with issue times and valid times; audit revisions | Pinned historical observations as outcome/reference evidence |
| Features | Enforce release before origin and the intended forecast horizon | Calendar facts that are known before the deadline |
| Splits | Design chronological or rolling-origin evaluation that respects availability | General rules against using later outcomes to fit earlier predictions |
| Recipe | Accept the new schema and handle missing forecasts | Candidate family as a proposal, not its old performance claim |
| Evidence | Fit and check a newly declared experiment only after the data exists | Old results under the original task label |

No new forecasting model or score is produced. Changing the label on an old result cannot make its weather inputs historically available. A timestamp check rejects a late observation and an unknown release time, while accepting an eligible constructed forecast; it does not fill the missing archive.
