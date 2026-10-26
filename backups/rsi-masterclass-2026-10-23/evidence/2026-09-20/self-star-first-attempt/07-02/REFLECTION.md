# Reflection before replay checks

Observed in the retained 09.05 trace: an unpruned regression tree reached training MAE 0 but had worse selection MAE than the linear parent. Hypothesis: fitting idiosyncratic training variation can hurt unseen-row prediction. Alternative: this task, sample, feature representation, or capacity choice may favor the parent; the trace alone does not identify a universal cause.

Proposed narrow rule: compare valid candidates on the declared selection metric and its direction; do not promote solely on training fit. Scope: same task, data role, and evaluator. Counterexample to an overbroad family ban: the retained nonlinear classification case. Check both replayed cases before retention. This is known evidence, not two fresh validation cases.
