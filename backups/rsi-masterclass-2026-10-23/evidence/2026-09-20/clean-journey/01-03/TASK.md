# Bike prediction task

One prediction estimates total rentals in one recorded hour. Target: cnt,
measured in rentals per hour. Use calendar fields for the first baseline.
Observed weather is available for later retrospective exercises, not evidence
of a day-ahead forecast. Exclude casual, registered, instant, and the raw target.
Use MAE; smaller is better. Train on 2011, select on the first half of 2012,
and reserve the second half for one final evaluation of a frozen recipe.
Fit transformations only on training data. The public source is UCI Bike
Sharing with repository-pinned attribution and checksums. This local split is
visible to the coding agent and is not a secret evaluation service.
