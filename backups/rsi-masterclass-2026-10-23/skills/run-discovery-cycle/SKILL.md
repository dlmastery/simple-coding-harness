---
name: run-discovery-cycle
description: Run a bounded ML discovery tree, revise its exploration policy through recorded-world replay, and deploy the selected version on later work. Use for the tabular discovery extension and Dream-style research exercises.
---

# Run a discovery cycle

Read the requested lesson and [the experiment guide](../../experiments/tabular-discovery/README.md).
Use the student's smaller lesson budget when one is specified. The maintainer's
larger research allocation does not replace a lab's limit. Students use plain
language; you write the implementation and run the commands.

## Keep the three objects distinct

- The pipeline predicts labels or numbers.
- The frozen proposer writes a child pipeline from an actual saved parent.
- The exploration policy chooses an unscored root or an observed leaf to continue.

In this supplied implementation the proposer is a deterministic program, not
an LLM discovery agent. You are the policy developer. State whether that role
shares context with earlier work. Do not describe it as an independent actor.

Use a new sibling workspace. Preserve existing workspaces, failures and final
locks. Read `rsi/tools/discovery_run.py` for its current interface. Its `task`
action permits only the six published development examples; these are known
course cases, not hidden evaluation tasks. `init` freezes data, policy, proposer,
runtime, attempt allowance and worker-process budget. Keep matching source to
resume; do not edit hashes to make a changed runtime accept an old experiment.

For the long Windows evaluation, the supplied
`how-did-i-generate-it/rsi/scripts/run_discovery_awake.ps1` helper requests
temporary idle-sleep prevention and releases it when the process ends. It does
not change persistent power settings. If a host interruption breaks an attempt,
preserve its original status and timing, inspect the system evidence, and
declare any replacement before evaluation. A result file alone does not justify
rewriting an observed timeout as success.

## Build and inspect a real tree

Run only the declared online allowance. Each child must copy and verify its
parent workspace before the proposer edits it. Record the parent, candidate
source, prediction rows, fit and process costs, and terminal outcome. A failed
attempt consumes resources. Retain the best observed candidate, which may be
an ancestor rather than the latest child.

Run the independent checker at
`how-did-i-generate-it/rsi/scripts/check_online_discovery.py`. Inspect a concrete
parent/child code change and its prediction check with the learner. Do not
infer successful inheritance from a drawn edge alone.

## Revise the policy against recorded worlds

Freeze the available trees. Write a proposal before each revision: observed
failure, evidence, proposed change, expected effect, risk and falsifier. Keep
the incumbent and every revision. A policy sees only the provided observations;
it cannot read hidden outcome files or identify a future task by its seed.

Use the same root-or-leaf interface for online work and replay. Root requests
reveal independent starts in recorded order. A non-root continuation must be
recorded. Unsupported requests stay unknown; never fill them with scores from
similar candidates. A tree truncated by early stopping has limited coverage.

Use the declared external ranking rule, with separate quality and cost
components. For the published extension this is normalized selection loss
plus 0.001 times represented worker-process seconds, over eight decisions per
world; unknown requests make a candidate ineligible. Exact ties retain the
incumbent. A smaller lesson can declare a smaller replay allowance before use.
The selector is `how-did-i-generate-it/rsi/scripts/select_discovery_policy.py`.

## Deploy and compare

Freeze the selected source before generating or inspecting later task data.
Use that exact version in the next online rollout. Add new trees to the history
only after those runs finish. Record promotion or retention honestly. The
incumbent can win; a retained policy is not a new improved generation.

For an effectiveness claim, compare procedures online on the same new tasks
under equal allocations. Keep final rows outside search workspaces and freeze
all choices before scoring them. Report predictive gains, ties, actual attempts,
worker time, failed work and development overhead separately. A known synthetic
grammar with new seeds tests instance transfer, not new-domain generalization.
If inference cost is unknown, do not claim net total-cost savings.

Stop at the declared limit. Save source lineage, replay coverage, actual later
use, predictions, checks and the next learning step. The full maintainer
evaluation is separately specified in the experiment guide; do not launch its
large allocation merely because a student asks to understand one tree.
