# Preserve the failed process-identity check

The original driver exited 1 at line 89 with `RuntimeError: Wrong live-process or ledger identity`. Its ready marker existed and the tool ledger said running. The lock recorded worker PID 29336. The driver compared that PID with its Popen launcher handle; it did not record the launcher PID before failing, so that number is unavailable.

Error cleanup killed its owned Popen process and recorded exit 1 in UNEXPECTED-CLEANUP.txt. The underlying worker was not queried before that cleanup; do not claim that the driver's intended direct-worker termination sequence passed.

After the failure, a Windows Win32_Process query for PID 29336 returned no process. The tool's .running file and running ledger remained, and trial-001 had no prediction or failure report. The fixture marker states that its replacement fit function was reached before estimator training. sys.executable points to the project's venv launcher; sys._base_executable points to the uv-managed Python runtime. The observed mismatch is consistent with a launcher/worker distinction, not proof of every Windows launch path.

Keep this attempt charged. Do not rerun the first driver or create a replacement experiment. A separate recovery script will inspect the lock's actual worker PID through the operating system, retain both refusal probes and state snapshots, reconcile the existing row, and use only the already allocated one real continuation fit. This is a stale-running-record exercise with a failed initial termination harness, not successful validation of that original driver.
