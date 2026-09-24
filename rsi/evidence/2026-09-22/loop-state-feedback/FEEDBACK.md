# Inspect a weakness, then test an input change

The existing linear/calendar selection report has hourly mean absolute error 260.203781 at hour 8 and 243.145544 at hour 17. Calendar categories improve the average over a constant predictor, but large errors remain at busy periods. These are measured error slices; they do not identify their cause.

Hypothesis: this fixed linear model may benefit from the permitted observed-weather fields, which describe variation not supplied by the calendar-only recipe. Test linear/calendar against linear/all with seed 17 and identical task, split and MAE. Expect lower overall selection MAE, but preserve a worse or mixed result if it occurs.

Alternative explanation: some residual error may come from interactions or changing demand that this linear model cannot represent. Adding weather can also add noise or expose shift; lower prediction error would not establish a causal weather effect.

The author has already seen prior public-data results for these recipes. This is a recorded execution of the teaching hypothesis, not a blind discovery or a new test of generalization. No final result will guide the choice. Both declared fits and their errors will be kept.

Decision: retain the calendar-only control, then add the allowed observed-weather feature group in the second candidate. The research procedure and model family remain fixed.
