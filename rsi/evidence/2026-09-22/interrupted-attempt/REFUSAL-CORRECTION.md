# Correct the expected exit without repeating the probe

The first recovery driver expected exit 1 for the stale-lock probe. The unchanged course CLI returned exit 2 with the intended “Workspace busy or interrupted” refusal. The driver's assertion therefore stopped recovery, even though the tool refused correctly. The preserved output records both observed 2 and mistaken expected 1.

Source inspection confirms the course CLI returns 2 for its Refusal/OSError handler. The historical journey controller used a different status convention. The corrective script checks the existing refusal output and unchanged ledger, then continues after that probe. It does not repeat the probe, recreate the workspace or spend another attempt. The second refusal expects the correct exit 2.

The first recovery script and command record are retained as recover-interrupted-attempt-first.py and RECOVERY-COMMANDS-FIRST.md. The later script is v2. No training has occurred before this correction.
