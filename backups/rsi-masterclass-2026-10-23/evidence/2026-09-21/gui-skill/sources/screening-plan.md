# Screen two estimator changes

The first study retains linear/all. Its remaining commuting-hour errors motivate two hypotheses: a tree can represent nonlinear input relationships, or an ensemble of trees can do so with less sensitivity to one tree's partitions. The candidates are the supplied tree/all and forest/all recipes. Both preserve the exact permitted feature group. No hyperparameter tuning or extra candidate is allocated.

Train the cheap screen on all records dated January–March 2011. Evaluate January 2012 only. Both candidates use seed 17, the same subset rows, preprocessing constructors, clipping, and MAE. Each gets one fit. Save the row lists before fitting. Numeric imputation/scaling and category encoding fit only on the training subset.

Advance the candidate with lower screening MAE; a tie favors tree. This ranks two candidates under this proxy. There is no fitted linear baseline on the subset, so do not claim either improves on that missing screen baseline. The winter-heavy subset also omits much of the year's variation and can select the wrong idea for fuller conditions.

After recording the advancement decision, fit only the selected estimator/all and linear/all using full 2011 training and January–June 2012 selection. The linear arm removes the selected estimator replacement. Its weather features remain. This matched pair tests the selected component; it cannot determine the unselected idea's full-condition score or ranking.

Accept the selected component if its fuller selection MAE is strictly below linear/all and both prediction checks pass. Otherwise keep linear/all. Four fits total: two screen fits and two confirmation/ablation fits. Final-partition rows are not used for fitting or scoring. Public source bytes remain readable and prior author exposure is recorded separately.
