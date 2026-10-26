# One fixed prediction, different errors

The original 00.03 ledger contains one successful constant/calendar fit with seed 17. The training median is 109 rentals. The saved selection predictions are all 109. No new fit was performed for this note.

For its first three selection rows, actual counts are 48, 93 and 75. Absolute errors are 61, 16 and 34; their mean is 37. These examples explain subtraction and absolute value. They are not the full selection MAE, which is approximately 159.947912 over 4,358 rows.

ERROR-EXAMPLES.csv also selects a quiet and a busy hour from the saved selection records. At source row 8718, hour 2, actual demand is 1: predicting 109 overestimates by 108. At row 10622, hour 17, actual demand is 957: predicting 109 underestimates by 848. These are deliberately chosen extremes, not representative average errors or evidence that every quiet/busy hour behaves this way.

The same prediction can err in opposite directions because the outcomes differ. Absolute error drops the direction. Later error-by-hour analysis can reveal a pattern that a single average hides; choosing a new model requires another declared experiment.
