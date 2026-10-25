# Outcome checks, frozen memory, and stale state

Author walkthrough for labs 10.04–10.06, executed on 21 September 2026. Four small Ridge fits ran on a new synthetic regression fixture. No student or separate coding-agent context participated.

The useful result is a boundary: a checked score does not validate an actor's lesson, and an unchanged memory file does not prove a clean memory comparison.

## Outcome and lesson

The unchanged result checker verified the earlier exploration trial-003: **selection MAE 99.175924**. It checked rows, targets, the ledger, and the report. This activity used one checker invocation and zero fits. See the [verdict](10-04/OUTCOME.md) and [execution record](10-04/EXECUTION.md).

After reading that verdict, the author wrote [MEMORY.md](10-04/MEMORY.md). It records the local weather-feature result and a scoped suggestion to inspect residuals before a bounded feature probe. The verifier did not write or approve this interpretation.

The [overbroad draft](10-04/OVERBROAD.md) says always to use the winning linear recipe. An [existing classification counterexample](10-04/COUNTEREXAMPLE.md) has selection balanced accuracy 0.86 for its linear parent and 0.88 for its tree child. This defeats a universal linear-model preference. It does not compare classification accuracy numerically with regression MAE or isolate the effect of selecting all features.

## Frozen comparison

The [protocol](PROTOCOL.md) allocated two fits per arm. Both used seed 61005, the same 480 generated rows, a 280/100/100 train/selection/evaluation split, StandardScaler, and Ridge(alpha=10). Preprocessing fitted only on training rows. The [task description](10-05/TASK.md) makes the synthetic target and host access explicit.

Both initial calendar fits had selection MAE 25.395112002 and selection residual/temperature correlation 0.950261481. After inspecting these observations, the author saved each [no-memory decision](10-05/no-memory/DECISION.md) and [memory decision](10-05/memory/DECISION.md) before the next fit. The declared threshold was 0.2; both added the weather group.

| Arm | Calendar selection MAE | Weather-added selection MAE | Frozen-choice evaluation MAE | Total fit seconds |
|---|---:|---:|---:|---:|
| No memory-file read | 25.395112002 | 7.158134494 | 7.027189070 | 0.005433 |
| Frozen memory-file read | 25.395112002 | 7.158134494 | 7.027189070 | 0.003516 |

The difference in evaluation MAE is **zero**. The [choices](10-05/CHOICES.csv) were frozen before evaluation predictions; retained, locally generated models supplied those predictions without refitting. Row IDs, targets, and MAE were checked again. Input, memory, and decision hashes remained fixed. Four fits ran, and all completed. Tiny fit-time differences are not evidence of a speed benefit; they exclude agent work and most orchestration time.

Both paths shared the residual rule. The same author had already read the memory when designing both paths. Therefore the no-memory path's lack of a file read is **not a clean agent information boundary**. See the [exposure record](10-05/EXPOSURE.md), [freeze](10-05/FREEZE.md), [results](10-05/RESULTS.md), and fit ledgers for [no-memory](10-05/no-memory/FITS.csv) and [memory](10-05/memory/FITS.csv). This run demonstrates file freezing and matched budgets, not a measured causal memory benefit. Agent costs and complete phase wall times were not recorded.

After evaluation, a [separately planned copy update](10-05/adaptation/PLAN.md) added that limitation to an adaptation copy. Its [hash changed while the original stayed fixed](10-05/adaptation/CHECK.md). Zero extra fits ran. This is a memory-write demonstration; adaptation performance remains unmeasured.

## Working state and experience

The next activity used a [clearly labelled state fixture](10-06/CONTRACT.md), not a new training run. Its simulated remaining budget authorizes no fits. [WORKING.md](10-06/WORKING.md) holds the new run's current state; [EXPERIENCE.md](10-06/EXPERIENCE.md) holds a scoped row-identity audit lesson.

Two retrieval checks ran. The [first accepted the declared experience record](10-06/RETRIEVAL-1.md) without changing working state. The [second rejected historical state](10-06/RETRIEVAL-2.md): both records name trial-001, but their run identities differ. This is a simple type-and-identity gate, not a test of general semantic retrieval.

A [merged copy](10-06/MERGED-COPY.md) exposes two run identities, conflicting pending actions, and two remaining-budget values. The [ambiguity note](10-06/AMBIGUITY.md) explains why concatenating the stores does not make a valid current plan. No third retrieval check or fit ran.

## Reproduce and inspect

Use the lesson's natural-language request to have your coding agent construct the activity in a new workspace with its own declared budget. This archive is evidence, not a folder to resume as an active experiment. The original workspace was `rsi-work-2026-09-21-memory-labs`, next to the repository.

The author driver has four guarded phases: outcome, probes, finish, and retrieval. It pauses after the first two fits so the actor can inspect the observations and record decisions. The driver refuses an existing completed phase. [Both driver revisions are preserved](DRIVER-REVISIONS.md); v2 adds the decision-hash check before any comparison fit runs. Actor-authored notes and the adaptation-copy action are separate from the driver.

The [manifest](MANIFEST.csv) records 68 original files, all checked against both the working copy and archive. The manifest and this explanatory README are outside that manifest. No source-paper reproduction, clean-context ablation, independent learner assessment, or LLM weight update is claimed.
