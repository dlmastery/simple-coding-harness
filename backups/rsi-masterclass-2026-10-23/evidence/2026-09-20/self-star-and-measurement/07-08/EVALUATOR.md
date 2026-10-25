# Fixed evaluator

For both input cases and both versions, accept a reported value only if it matches the same pinned-prediction MAE within 1e-9. Never edit this rule to make the child pass. Retain the child only if it fixes the wrong input without breaking the correct input.
