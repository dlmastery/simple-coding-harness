# Two fresh contexts

The user resumed the prepared two-session test on 23 September 2026. Both
collaboration agents were launched with `fork_turns: none`, with no model
override. Their task names are `/root/complete_handoff` and
`/root/missing_handoff`. The host returns task names, not provider billing or
proof of filesystem isolation.

Before dispatch, the parent recorded the repository commit, dependency versions,
and SHA-256 identities of the tool, data and packet files. See
[the frozen inventory](PRE-DISPATCH-SOURCES.csv) and [dispatch timestamp](DISPATCH.md).

The complete agent received the complete packet path, pinned repository revision,
project Python path, and a new sibling output path. Its prompt limited it to one
baseline attempt, a real 60-second subprocess timeout, no retry or final scoring,
and prediction checks. It prohibited reading previous results, other packets,
repository changes, publishing, delegation and external messages.

The missing-task agent received only its packet and sibling output paths. Its
prompt allowed reading only the two packet files, required a skill hash and
missing-input report, and prohibited model fits, other repository reads,
invented choices, repository changes, publishing and delegation.

Both prompts required actual command/output records, visible host context,
and skipped learner responses. No expected score or old prediction was supplied.
They share the filesystem and installed dependencies with the parent. File
access restrictions here are instructions, not an enforced sandbox. Their
read ledgers are self-reported; they are not an OS-level access audit.

This is an author walkthrough in the existing agent host. It cannot establish
cross-provider portability, student comprehension, security isolation or
adaptive improvement. The unchanged skill is being reused, not optimized.

The archived child command records and final reports are the available traces.
They must not be described as a complete provider-level inference transcript.
