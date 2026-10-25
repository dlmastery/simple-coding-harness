# Decision before fit three

Model: linear
Features: all
Hypothesis: Adding the permitted weather group to the calendar Ridge model will reduce selection MAE compared with linear/calendar; the test keeps model family, seed, split, metric, and estimator settings fixed.

The two probe scores are 159.947912 and 109.807668. In the calendar model's selection residuals, weather categories 1, 2, and 3 have 2,950, 1,058, and 348 rows. Their mean signed residuals are 106.095167, 72.210436, and -17.348482. The range, 123.443650 rentals per hour, exceeds the predeclared threshold of 10. Category 4 has only two rows and is excluded by the minimum-count rule.

The hourly summary also shows substantial remaining error near 08:00. Weather categories may correlate with hour, season, or demand shifts; this is not a causal estimate. The final fit answers whether this permitted feature-group addition helps this fixed linear recipe on the selection partition. It cannot establish that weather is the sole missing mechanism, that every weather feature helps, or that the inputs exist at a real forecast origin.

One fit remains. No final evaluation was consulted for this decision. The author has seen earlier course results, so this is a transparent execution of a fixed exploration rule, not a blind discovery. No task-memory file was loaded. A worse result will be retained.
