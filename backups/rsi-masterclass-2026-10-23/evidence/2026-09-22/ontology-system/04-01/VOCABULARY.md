# Ten objects from one baseline

The reference is the saved 01.02 fixed-process baseline from 22 September. Names refer to that workspace, not every file called trial-001 elsewhere.

| Object | Type | Meaning | Concrete evidence |
|---|---|---|---|
| Pinned hourly bike table | Dataset | The collection of recorded hourly observations | hour.csv, identified by the experiment's data checksum |
| hr | Column | One recorded value per row: hour of day | Source schema and permitted calendar inputs |
| cnt as the quantity to predict | Target role | The scientific role assigned to the total rental-count column | TASK.md and the bike contract; casual and registered cannot supply it as inputs |
| Selection rows | Partition | Rows used to compare candidates after training | 2012-H1; 4,358 source identities in predictions.csv |
| constant/calendar/seed 17 | Recipe | Instructions that can be executed more than once | PROPOSAL.md and ledger model/features/seed fields |
| Learned constant 109 | Fitted task model | The result of fitting the training-median estimator | Runtime object and constant saved predictions; no serialized model file was retained by this runner |
| MAE | Metric | Mean absolute difference between targets and predictions | Independent checker implementation; lower is better |
| 159.94791188618632 rentals per hour | Measurement | A value of MAE for one candidate on one partition | trial-001 selection report and recomputed predictions |
| predictions.csv | Prediction artifact | Saved source identities, targets, estimates and hours | Its SHA-256 is 0004513ae666f36bcf4987e2b36944f1c4a8d79bf949ef09b788d0b95e6af93c |
| The recorded fit invocation | Fitting event | An action at a particular time under a contract | The fixed-process fit-command.txt and one-entry trials.csv |

A recipe can have two fitting events and two runtime model objects. Equal prediction bytes do not make the events identical. MAE is a rule; 159.94791188618632 is one result of applying that rule. A target is a role in a question, not merely a special storage format.

The fitted model no longer exists as a live object in this evidence folder. Its recorded recipe, execution and predictions support the limited statement above; the illustration must not be read as a promise of a saved weights file.
