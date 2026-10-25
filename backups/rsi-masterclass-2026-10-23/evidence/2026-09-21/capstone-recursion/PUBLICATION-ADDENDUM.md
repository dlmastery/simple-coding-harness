# Progress-message correction after sealing

During publication review, the inherited runner's experiment/PROGRESS.md still said final evaluation was unused. That message describes its last fit, not the later terminal phase. The actual FINAL-LOCK.md, terminal command log, FINAL-RESULTS.csv and top-level PROGRESS.md record the completed evaluation and closed budget. No extra fit or evaluation occurred.

The original file and 121-file manifest remain unchanged. The maintained recursive_control.py now writes a closed status after successful terminal evaluation in future runs. That one-line reporting change was inspected but not executed in this sealed experiment; the archive's frozen controller is the exact version that ran. This addendum and the archive README were added after sealing and are outside the original manifest.

The author environment did not expose a per-experiment coding-agent inference cap or billing. Eight CPU fits and 60-second subprocess limits were enforced; inference cost and limits remain unavailable. This is not equal measured total research cost across arms.
