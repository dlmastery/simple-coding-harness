# Does observed weather help this linear predictor?

The copied earlier calendar-only linear result has selection MAE 109.807668 rentals per hour. Its error is large at commuting times: about 260.20 at hour 8 and 243.15 at hour 17. Calendar indicators describe recurring patterns but cannot identify weather differences between otherwise similar hours.

Hypothesis: adding the permitted observed-weather fields to the fixed linear recipe will reduce overall January–June 2012 selection MAE by at least 5% relative to calendar-only inputs. Weather may explain some demand variation that the calendar fields miss. This is a predictive hypothesis, not a causal explanation established by the comparison.

Baseline: supplied linear/calendar. Intervention: supplied linear/all. Train both on 2011, use seed 17 and the same Ridge/preprocessing settings, and evaluate the fixed selection rows with MAE. Fit each once, two fits total. Preserve hourly error slices as descriptive evidence; they are not additional success criteria selected after the result.

Reject the stated 5% hypothesis if the relative MAE decrease is below 5%, zero, or negative. A smaller positive decrease can support a narrower observation, but does not pass this declared threshold. An invalid prediction check leaves the comparison unresolved.

Alternative explanation: the additional fields may proxy time-dependent patterns or interact with misspecification of the linear model. Even a favorable comparison cannot establish that changing weather causes a specified change in rentals, that the effect transfers to another city, or that these observed fields were available for an advance forecast.

The author has already seen results on these development data. This document freezes the question before this run's repeated fits; it is not a blind preregistration of a previously unknown result. No final model evaluation is requested.
