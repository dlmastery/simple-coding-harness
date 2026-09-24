# A stopped worker still spent an attempt

Lab [02.05](../../../02_loop_engineering/step_05_resume/README.md) already has an [orderly checkpoint](../../2026-09-20/clean-journey/02-05/CHECKPOINT-1.md), three completed fits across processes, and an exhausted-budget refusal. This supplement executes the additional stale-running teaching case in a separate experiment.

The [result](RESULT.md) preserves two author-driver errors: a launcher/worker PID mismatch and an incorrect expected refusal status. Neither resets the experiment. The recorded worker was confirmed absent through the operating system; both stale-lock and unresolved-running-record requests were refused before admission. The author reconciled trial-001 as interrupted, then one real linear/calendar continuation ran as trial-002 with selection MAE 109.807668.

| Inspect | Evidence |
|---|---|
| Declared allocation | [Protocol](PROTOCOL.md): one no-training fixture, one real fit, two refusal probes, one prediction check |
| What failed first | [Original driver failure](FIRST-DRIVER-FAILURE.md), [cleanup output](UNEXPECTED-CLEANUP.txt), [refusal-status correction](REFUSAL-CORRECTION.md) |
| Why the lock could be removed | [Original lock](LOCK-BEFORE.txt), [OS check before removal](OS-WORKER-CHECK-BEFORE-REMOVAL.txt) |
| No budget reset | [Original running ledger](LEDGER-BEFORE.csv), [reconciled ledger](LEDGER-RECONCILED.csv), [final two-row ledger](experiment/trials.csv) |
| Actual refusals | [Stale lock](stale-lock-refusal-output.txt), [unresolved record](running-record-refusal-output.txt) |
| Actual continuation | [Command output](real-continuation-output.txt), [checked predictions](experiment/trial-002/CHECK.md), [nine invariants](CHECKS.csv) |
| Reconstruct the path | [First recovery command](RECOVERY-COMMANDS-FIRST.md), [later commands](RECOVERY-COMMANDS.md), [source identities](SOURCE.md), [progress](PROGRESS.md) |

Two of three slots are consumed. Only one estimator fit occurred. The unused slot is not permission to continue this completed allocation. Training-state resumption, a fresh coding-agent context, and remote backends remain untested. The original failed PID assumption is explicitly not validated.

The [manifest](MANIFEST.csv) preserves the original run files and failed scripts. This navigation page was added after sealing. The historical experiment and its final lock remain unchanged.
