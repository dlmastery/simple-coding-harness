# Cross-platform course checks

Date: 20 September 2026.

The [RSI workflow](../../../.github/workflows/rsi.yml) installs the four documented course dependencies in a clean GitHub runner. It runs the behavior tests, local Markdown link checks, student snippet discovery, and lesson publisher. It then checks that publishing did not change the tracked course pages. The matrix uses Python 3.12 on Linux, macOS, and Windows. Each job records the actual Python, package, and Node versions.

This check does not use the repository's unrelated SDK dependencies. It does not replace the existing repository-wide workflow. Matrix jobs continue independently after a failure so that one platform cannot hide another platform's result.

## Why this check was added

The repository-wide [run at fef7431](https://github.com/dlmastery/simple-coding-harness/actions/runs/35506432361) failed. Its completed Ubuntu/Python 3.10 job reported 15 passing RSI behavior tests and successful RSI publication checks. Failures were reported in `step_48_trueforge_sandbox_skills` and two `genui/02_ag_ui` sections. Several remaining matrix jobs were cancelled by fail-fast.

The planning-only [run at 2d02635](https://github.com/dlmastery/simple-coding-harness/actions/runs/35495673617) also failed before the rebuilt runtime was introduced. Direct job-log inspection confirmed the same three affected sections and the same error families: `SyncPager.data`, `AddOperation` compared with a dictionary, and `ReplaceOperation` used as a dictionary. Failure counts differ across the runs; this establishes prior occurrence, not a full diagnosis of those courses. No unrelated tests have been suppressed or changed.

Retained [planning-run excerpts](aggregate-ci-planning-excerpt.txt) and [fef7431 excerpts](aggregate-ci-fef7431-excerpt.txt) contain only matching failure and RSI result lines from the public job logs. The full logs remain at the linked runs. An initial `gh run view --log-failed` read returned no text for the planning run; fetching its job log directly supplied the evidence.

## Results

The dedicated [run at eceeeab](https://github.com/dlmastery/simple-coding-harness/actions/runs/35506978384) passed on all three platforms. Exact tested commit: `eceeeab64aa37206355f6b840b28c4d30c938c3f`. The run completed on 20 September 2026 at 11:09:15 UTC.

| Hosted runner | Actual Python | Behavior tests | Publication and publisher |
|---|---|---|---|
| Ubuntu | 3.12.14 | 15 passed in 4.00 seconds | 101 lessons; 1,601 links; no issues; clean generated diff |
| macOS | 3.12.10 | 15 passed in 1.80 seconds | Same checks passed |
| Windows | 3.12.10 | 15 passed in 2.70 seconds | Same checks passed |

All three resolved NumPy 2.5.3 and SciPy 1.18.1 alongside the four pinned direct dependencies. Node was 22.23.2. These actual patch versions differ from the author's Python 3.12.12 environment. Declaring Python 3.12 support does not mean every environment used the same patch version.

Retained selected job logs: [Linux](ci-eceeeab-linux.txt), [macOS](ci-eceeeab-macos.txt), [Windows](ci-eceeeab-windows.txt). The [machine-generated run metadata](ci-eceeeab-status.txt) includes job outcomes and URLs; it is provenance, not a student configuration file. Every matrix job also passed snippet discovery and its final generated-page check. Broader repository CI still has the separately documented failures.

Before pushing, the local equivalent passed: 15 tests, 101 lessons, 1,599 local targets, no publication problems, and a clean generated-page diff. Snippet discovery found all 101 labs and no runnable student code blocks; it is not evidence of 101 executed activities.

A passing matrix establishes the checked runtime and publishing behavior on those hosted runners. It does not establish student learning, execution of all 101 prompts, native support for another coding agent, a measured minimum laptop specification, or GPU/cluster support.
