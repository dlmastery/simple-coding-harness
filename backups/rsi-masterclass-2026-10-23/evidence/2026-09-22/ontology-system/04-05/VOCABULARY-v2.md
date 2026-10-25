# Prediction issued before the target hour

Predict tomorrow's noon rental count at noon today. Every input must have a known release timestamp at or before today's origin. An observation of tomorrow's weather arrives too late. A forecast issued before the origin might qualify, but its forecast horizon and target location must also match. Release-time eligibility alone does not establish forecast quality.

The availability fixtures use explicit UTC timestamps in September 2026. They are constructed records for this rule, not fields recovered from the historical bike dataset. The task's actual archived forecast source remains missing.
