---
name: dgm-meta
description: The Darwin Goedel Machine lineage - rewrite the actor pack's own source (its SKILL.md and loop.json), one generation deep, from a parent chosen in an archive of variants scored on a fixed held-out benchmark, behind the private gate and the human cycle. Use in rsi/step_14_rsi_self_modifying, one generation per visit.
metadata:
  type: workflow
  version: "2.0"
  rsi: "on"
  approval: both
  patches: ["SKILL.md", "loop.json"]
---
# The Darwin Goedel Machine lineage: the agent's own source, with an archive of stepping stones

Run every command through the Bash tool from this lesson's directory. This
pack's directory is `.claude/skills/dgm-meta` (`M`); the target is the actor
pack `.claude/skills/adult-income` (`P`); the verifier is
`.claude/skills/adult-income-verifier` (`V`); the held-out benchmark is
`M/held-out/` (two synthetic tables no curriculum or exam problem uses); `T`
is the last held-out task, `M/held-out/02_pool_trees_2.json`.

## Boot order
1. This file. 2. `tools.md`. The log, the pack and the archive come through scripts.

## Procedure - one generation
1. Run the current variant on the held-out benchmark: for each task under `M/held-out/`, in order, follow `P/SKILL.md` for the control arm (`--arm control --memory off`) and for the memory arm (with `--seed <g>`, where `g` is this generation's number, on every command), then `V/SKILL.md` on that task. Both arms and the verifier on both tasks.
2. Archive the variant with its held-out score:
   `python ../tools/archive.py --pack M --task T --target P --action add --label gen<g>-<current policy> --held-out M/held-out --seed <g>`
   The score is, over the held-out tasks, the private score of the memory arm's best recipe minus the control arm's, averaged: a gain over the static walk on a fixed benchmark.
3. Choose the parent: `python ../tools/archive.py --pack M --task T --target P --action parent`. The parent is the variant with the best held-out score, ties to the older one; it is not the latest by default. If `is_latest` is false: `python ../tools/archive.py --pack M --task T --target P --action restore --label <parent>`, then `python ../tools/read_pack.py --pack P --checksums`; you now stand on the parent.
4. Propose ONE rewrite of the parent's source: the `Search policy:` line of `SKILL.md` and the `policy` field of `loop.json` set to the first of `static`, `obey-memory`, `neighbours-of-top-3`, `prefer-untried-family` that `policies_in_archive` does not hold (nothing to propose when all four are there: say so and stop). Write both files under `runs/dgm-meta/patch/` (use your Write tool) and:
   `python ../tools/patch_pack.py --pack M --task T --target P --files @runs/dgm-meta/patch --recipe model=<m>,hyper=<h>,scale=<s>,encode=<e>,class_weight=<c> --summary "gen<g+1>: <policy> from <parent>" --visit <g>`
   with the parent's best held-out recipe (the memory arm's best val recipe on `T`) as the evidence recipe. `patches:` allows those two files only. `approval: both`: the private gate decides keep-or-rollback first; if it kept the rewrite, show the user the diff and ask **approve / edit / reject**, wait, and land their answer:
   `python ../tools/patch_pack.py --pack M --task T --target P --proposal <id> --approved "<the user's exact words>"`
5. Answer in text with the archive (labels, held-out scores, parent), the rewrite and the verdicts. Stop. The next visit is generation `g + 1` on the rewritten pack.

## Rules
- One generation deep: a rewrite of the parent, never of a rewrite that has not run the benchmark.
- A variant that lowered the held-out score is in the archive with its score; the parent rule never picks it over a better one. A rewrite the gate rejected never runs and never enters the archive.
- You never fit for yourself and never score the test split: `fit_recipe.py` and `score_test.py` for the meta pack are refused; the actor's arms in step 1 are run as the actor.

## Done when
`archive.py --action add` holds this generation's variant and `patch_pack.py` has answered, or every policy is in the archive.
