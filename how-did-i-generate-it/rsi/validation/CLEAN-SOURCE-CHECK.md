# Clean-source check

On 20 September 2026, exported Git commit `93d3760a14a9940df23e26bc67bdf7cb22e30933` with `git archive --format=zip` and expanded it into a new sibling folder, `work/rsi-clean-93d3760`. Neither the existing working tree nor its ignored cache folders supplied course source files to this checkout.

Ran the exported `run_tests.py rsi` through the already installed project Python 3.12.12 environment. All 15 tests passed in 4.52 seconds. Publication checks found 101 lessons, 1,255 local targets, and zero problems at that checkpoint.

Ran the exported `rsi/tools/lab.py run` with bike, constant model, calendar features, and a new workspace. The actual result was MAE 159.94791188618632, with 0.108135 recorded fit seconds. The saved predictions passed recomputation. [Evidence](../../../rsi/evidence/2026-09-20/clean-source-baseline/CHECK.md).

This checks clean source content and a fresh result directory. It reuses the installed Python environment; it is not a clean dependency installation, another operating system, another coding agent, or a learner study. The archive and expanded folder are local reproducible copies of the identified Git commit, not separate authored deliverables. Result artifacts are checked in.

## Fresh dependency installation

A second check created a new `.venv` inside the exported source using `uv venv .venv --python 3.12.12`. Installed the documented requirements with `uv pip install --python .venv/Scripts/python.exe -r rsi/tools/requirements.txt`. All 24 packages installed successfully. Running `run_tests.py rsi` in that environment passed all 15 tests in 12.22 seconds, with the same 101-lesson publication check. The [resolved package list](clean-source-environment.txt) is retained.

This second check establishes fresh environment setup on this Windows host. It does not establish another operating system, another coding agent, or a learner study.
