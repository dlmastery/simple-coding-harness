# Move the contract before making the job larger

Status: generated plan only. No remote backend was supplied or run. Current authorization covers the local capstone checks, not paid compute.

First portability job: the same median baseline with the same white-wine bytes, split, package, seed policy, and evaluator. Proposed ceiling: one CPU process, at most four allocated CPU cores, 8 GB memory, ten minutes including collection, one attempt, and no paid spend. Actual host, connection profile, scheduler queue, storage paths, pricing, and capacity are unknown. The agent must resolve them and generate the backend-specific launch files before submission. No credentials belong in this document.

Keep candidate and attempt identifiers with data, package, split, and evaluator hashes. Record scheduler job ID, queued/running/terminal events, wall time, allocation, retries, predictions, and validation. Use an idempotency key or scheduler metadata to reconcile a lost submission response before trying again.

Cancellation must target the recorded job ID and be followed by an observed stopped state. The tiny scikit-learn model has no mid-fit checkpoint. A cancelled fit remains charged; a retry needs a separately allocated attempt. Test cancellation on a harmless slow job before calling that backend supported.

A genuinely larger task requires a new brief: data permission and scale, model family, accelerator type/count, concurrency, total attempts, time/GPU-hour/monetary limits, checkpoint contents, and held-out evaluation. For an iterative GPU model, include optimizer, progress, RNG, and data-order state, then verify resumed training under the intended protocol. More hardware does not make the current 4,898-row task a meaningful foundation-model experiment.

Before a large launch, run the same local contract checks and a tiny actual backend job. Report generated-only, inspected, and executed capabilities separately. This plan provides the handoff fields; it does not pretend to implement a scheduler that has not been chosen.
