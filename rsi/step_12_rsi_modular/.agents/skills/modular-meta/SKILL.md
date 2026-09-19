---
name: modular-meta
description: ModularRSI's meta pack - localise a harness bug to one module by contrasting two actor packs on a benchmark-disjoint pool, patch that one module of the losing pack with the winning text, and validate on the pool's private split before it lands. Use in rsi/step_12_rsi_modular after both actors have run every pool task.
metadata:
  type: workflow
  version: "2.0"
  rsi: "on"
  approval: gate
  patches: ["modules/*.md"]
---
# ModularRSI's meta pack: a module, evolved off the benchmark

Run every command through the Bash tool from this lesson's directory. This
pack's directory is `.claude/skills/modular-meta` (`M`); the two actors are
`.claude/skills/actor-a` (`A`) and `.claude/skills/actor-b` (`B`); the target
is the losing one; the pool is `pool/` (two synthetic tables no curriculum or
exam problem uses); the task file of the last pool task is `T`.

## Boot order
1. This file. 2. `tools.md`. The pool logs and the two packs come through scripts.

## Procedure
1. The pool run, both actors, memory arms only, in pool order (`pool/01_pool_trees_1.json`, then `pool/02_pool_trees_2.json`): for each pool task, follow `A/SKILL.md` then `B/SKILL.md` (each pack's five modules), then the verifier `.claude/skills/adult-income-verifier/SKILL.md` twice - once with `--pack A`, once with `--pack B` - so both actors carry the same cards into the next pool task.
2. Contrast the two actors over the pool:
   `python ../tools/contrast.py --pack M --task T --a A --b B --tasks pool`
   The script pairs, per pool task both actors ran, the success (higher best val) with the failure, names the one `modules/*.md` file whose text differs between the two packs (`module`), returns both texts, and the `winner`.
3. If `winner` is null, or `module` is null (no single module differs, or several do), say so and stop: the bug is not localised.
4. Otherwise write the loser's differing module with the winner's text under `runs/modular-meta/patch/modules/<file>` (use your Write tool) and patch the loser:
   `python ../tools/patch_pack.py --pack M --task T --target <the loser> --files @runs/modular-meta/patch --recipe model=<m>,hyper=<h>,scale=<s>,encode=<e>,class_weight=<c> --summary "<module> <- <winner>'s text" --visit 1`
   with the winner's best pool recipe as the evidence recipe. `patches: ["modules/*.md"]`: the script refuses any other file. `approval: gate`: the private split of the pool task decides - keep, or roll back. The eval table is never used.
5. Answer in text with the contrast result (pairs, module, winner), the gate's verdict and the version label. Stop.

## Rules
- One module per patch. The validation split is the pool task's private split; the eval table (`../tasks/`) is never used for validation.
- You never fit and never score the test split: `fit_recipe.py` and `score_test.py` are not in your `tools.md`.

## Done when
`contrast.py` has answered and, if a patch applied, `patch_pack.py` has answered once.
