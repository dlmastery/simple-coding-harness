# Outcome, frozen memory, and memory lifetimes

Author walkthrough for 10.04–10.06, 21 September 2026. Use a new sibling workspace. No learner participates. The same author designs both evaluation arms; no clean no-memory information boundary is claimed.

## 10.04: one outcome, one memory statement

Run the unchanged result checker once on exploration trial-003 in its original workspace. Save its new verdict outside that experiment. Zero fits. Then the task actor writes MEMORY.md with a local finding and a scoped procedure suggestion. The verifier neither writes nor approves that text. Inspect one already executed counterexample to an overbroad “always use the winner” statement. Preserve both the overbroad draft and bounded memory. No new counterexample fit.

## 10.05: a matched, shared-context demonstration

Freeze MEMORY.md before generating a fresh synthetic regression fixture: seed 61005, 480 rows, calendar inputs (sine/cosine hour and weekend), temperature and humidity, with synthetic demand as the target. Fixed row roles: 280 train, 100 selection, 100 evaluation. This is an authored numerical fixture, not real bike data or a blind task. The generator and labels are visible to the host.

Each arm receives two fits: Ridge(alpha=10) on calendar, then one optional feature-group addition to the same estimator. Four fits total, no refits for evaluation. The initial fits run first. Save selection residual summaries before the actor writes each follow-up decision. The common strategy permits inspecting residuals against unused allowed features. Both arms receive that same strategy. The memory arm additionally reads the frozen memory file; the no-memory execution path does not read that file, but the author context has already seen it. Record this exposure rather than claiming isolation.

Apply the same criterion in both arms: if absolute selection residual correlation with temperature exceeds 0.2, add the weather group; otherwise repeat calendar to check reproducibility under an explicitly permitted second fit. Record the decision before fitting. Keep all unsuccessful or weak results. Select the lower selection-MAE recipe, ties favoring the baseline, and freeze both choices before predicting on evaluation rows with the already fitted models. The memory remains unchanged throughout. Measure fit and process time separately; agent costs are unknown.

The extra adaptation activity allows one actor-written update to a separate memory copy after the comparison, with zero extra fits. Record its changed hash and unchanged frozen original. This demonstrates a different update contract; it does not measure an adaptation performance benefit.

## 10.06: two retrieval checks

Use the actual completed exploration record as historical evidence. Create a clearly labelled partially completed state fixture for a new run. Its remaining-fit value is simulated state, not permission to execute a fit in this no-fit lab. Retrieve one scoped experience note while initializing working state from the new contract. Then present a stale working-state record whose candidate label collides with the current one but whose run identity differs; require rejection. Merge stores in a labelled copy and identify the conflicting state instruction without executing it. Preserve raw traces and run budgets.

Keep phase guards, before-action records, source snapshots, input and memory hashes, predictions, metrics, decisions, failed checks, timings, and manifests. A phase must not rerun completed fits. Stop on a changed frozen input, unexpected phase state, timeout, or budget exhaustion. All scientific claims remain limited to the executed local protocol.
