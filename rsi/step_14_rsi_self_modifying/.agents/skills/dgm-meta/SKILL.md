---
name: dgm-meta
description: "The Darwin Goedel Machine lineage - rewrite the actor pack's own source (its SKILL.md and loop.json), one generation deep, from a parent chosen in an archive of variants scored on a fixed held-out benchmark, behind the private gate and the human cycle. Use in rsi/step_14_rsi_self_modifying, one generation per visit."
metadata:
  type: workflow
  version: "3.0"
  rsi: "on"
  approval: both
  patches: ["SKILL.md", "loop.json"]
---
# The Darwin Goedel Machine lineage: the agent's own source, with an archive of stepping stones

Run every helper through the Bash tool from this lesson's directory. This pack's directory is
`.claude/skills/dgm-meta` (`M`); the target is the actor pack `.claude/skills/adult-income` (`P`);
the verifier is `.claude/skills/adult-income-verifier` (`V`); the held-out benchmark is
`M/held-out/` (`01_heldout_1/intent.md`, `02_heldout_2/intent.md`: two synthetic tables no
curriculum or exam problem uses); `T` is the last held-out task, `M/held-out/02_heldout_2`.

## Boot order
1. This file. 2. `tools.md`. 3. `M/config.md`. The log, the pack and the archive come through helpers.

## Procedure - one generation
1. Build `archive`, `read_pack`, `propose`, `gate`, `private_score`, `apply` and `rollback` under `runs/dgm-meta/helpers/` if they are not there yet.
2. Run the current variant on the held-out benchmark: for each task under `M/held-out/`, in order, follow `P/SKILL.md` for the control arm (`--arm control --memory off`) and for the memory arm (with `--seed <g>`, where `g` is this generation's number, on every command), then `V/SKILL.md` on that task. Both arms and the verifier on both tasks.
3. Archive the variant with its held-out score: `archive M T --target P --action add --label gen<g>-<current policy> --held-out M/held-out --seed <g>`. The score is, over the held-out tasks, the private score of the memory arm's best recipe minus the control arm's, averaged: a gain over the static walk on a fixed benchmark.
4. Choose the parent: `archive M T --target P --action parent`. The parent is the variant with the best held-out score, ties to the older one; it is not the latest by default. If `is_latest` is false: `archive M T --target P --action restore --label <parent>`, then `read_pack P`; you now stand on the parent.
5. Propose ONE rewrite of the parent's source: the `Search policy:` line of `SKILL.md` and the `policy` field of `loop.json` set to the first of `static`, `obey-memory`, `neighbours-of-top-3`, `prefer-untried-family` that `policies_in_archive` does not hold (nothing to propose when all four are there: say so and stop). Write both files under `runs/dgm-meta/patch/` (your Write tool) and `propose M T --target adult-income --files runs/dgm-meta/patch --recipe <the parent's best held-out recipe> --summary "gen<g+1>: <policy> from <parent>" --visit <g>`. `patches:` allows those two files only.
6. `approval: both`: first `gate M T <id>` - the private split of `T` decides keep-or-rollback; if it kept the rewrite, show the user the diff and ask **approve / edit / reject**, wait, and land their answer: write their words to `runs/dgm-meta/<task>/proposals/<id>.approved` and `apply M T <id> --approved "<the user's exact words>"` (a reject after the gate kept it: `rollback adult-income <version>`; the variant never enters the archive).
7. Answer in text with the archive (labels, held-out scores, parent), the rewrite and the verdicts. Stop. The next visit is generation `g + 1` on the rewritten pack.

## Rules
- One generation deep: a rewrite of the parent, never of a rewrite that has not run the benchmark.
- A variant that lowered the held-out score is in the archive with its score; the parent rule never picks it over a better one. A rewrite the gate rejected never runs and never enters the archive.
- You never fit for yourself and never score the test split: `fit_recipe` and `score_test` are forbidden to the meta pack; the actor's arms in step 2 are run as the actor.

## Off switch
META_OFF: `meta: off` in `M/config.md`; the archive is read and nothing is rewritten.

## Done when
`archive --action add` holds this generation's variant and `apply` has answered (or the gate rolled back), or every policy is in the archive.
