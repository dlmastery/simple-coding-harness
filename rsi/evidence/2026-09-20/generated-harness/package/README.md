# Generated bike research harness

This package was generated from [the readable brief](../HARNESS-BRIEF.md) using the course builder skill. The builder remains a separate procedure. This package runs a bounded task; it does not improve its builder.

Tell a coding agent: “Read this README and the brief. Run one baseline in a new sibling workspace, then show me its checked evidence.” The agent supplies paths and commands. Use the course Python 3.12 environment and `rsi/tools/requirements.txt`; no new package is required.

The agent invokes `run.py` with `--repo`, `--workspace`, and `--hypothesis`. Default model is constant and default feature group is calendar. An explicit candidate can use the supported shared-tool model and feature names. The wrapper fixes bike regression and limits each workspace to two attempts, including failures. It checks successful predictions before reporting a checked score.

Read [the workflow and recovery rules](WORKFLOW.md). The package depends on the identified course checkout; it is not a vendored standalone library. A handoff must include that checkout, the package, source data, and environment versions.

The wrapper and shared tool record their versions. These are cooperative local checks, not a tamper-proof boundary against an agent that can edit all files.
