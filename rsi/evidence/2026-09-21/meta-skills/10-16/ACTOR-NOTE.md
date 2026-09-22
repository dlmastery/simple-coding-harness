# Apply frozen v0 to the first task failure

I read META-SKILL-v0 and the two executed parent records. The seconds case selects A correctly. In the target case, the parent treats 800 milliseconds as 800 seconds and selects B at one second. The intended A runtime is 0.8 seconds. The missing conversion causes this decision.

Following v0's focused proposal instruction, add only Seconds per millisecond: 0.001 to the task skill. Keep the MAE-first ordering, tie rule, existing second conversion, and unknown-unit fallback. This repairs a known unit; it does not make the fallback sound. Execute the target and previously passing seconds case under the unchanged updater. Do not infer recursion from the task revision.
