# A proposed next policy, not another result

The online task retained linear recipe B under P0 (evaluation MAE 2.090287890) and tree recipe C under P1 (12.318137610). P0 remains the baseline and replay winner. P1's substantially larger errors motivate inspecting whether its piecewise-constant predictions approximate this smooth target poorly; that is a hypothesis, not a checked causal diagnosis.

Proposed P2: start with a linear candidate. Use training and selection residual diagnostics to decide whether one bounded residual-tree correction is justified. This proposal changes the initial allocation and the second-fit recipe. Keep its cost and changed candidate set explicit in any future comparison; do not pretend that it is the same two-order experiment.

This proposal has not been implemented, selected, or fitted. A future test needs a separately declared budget, fixed P2 instructions, matched comparison resources, and fresh task conditions that did not supply this feedback. Reusing the current evaluation rows to select P2 would turn them into development data. No further fits are permitted in this run.
