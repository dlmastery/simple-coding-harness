---
name: modular-meta
description: "ModularRSI's meta pack - localise a harness bug to one module by contrasting two actor packs on a benchmark-disjoint pool, patch that one module of the losing pack with the winning text, and validate on the pool's private split before it lands. Use in rsi/step_12_rsi_modular after both actors have run every pool task."
metadata:
  type: workflow
  version: "3.0"
  rsi: "on"
  approval: gate
  patches: ["modules/*.md"]
---
# ModularRSI's meta pack: a module, evolved off the benchmark

Run every helper through the Bash tool from this lesson's directory. This pack's directory is
`.claude/skills/modular-meta` (`M`); the two actors are `.claude/skills/actor-a` (`A`) and
`.claude/skills/actor-b` (`B`); the target is the losing one; the pool is `pool/` (two synthetic
tables under `pool/01_pool_trees_1/` and `pool/02_pool_trees_2/`, each with its `intent.md`, that no
curriculum or exam problem uses); `T` is the last pool task.

## Boot order
1. This file. 2. `tools.md`. 3. `M/config.md`. The pool logs and the two packs come through helpers.

## Procedure
1. Build `contrast`, `read_pack`, `propose`, `gate`, `private_score` and `rollback` under `runs/modular-meta/helpers/` if they are not there yet.
2. The pool run, both actors, memory arms only, in pool order: for each pool task, follow `A/SKILL.md` then `B/SKILL.md` (each pack's five modules), then the verifier `.claude/skills/adult-income-verifier/SKILL.md` twice - once with `--pack A`, once with `--pack B` - so both actors carry the same cards into the next pool task.
3. Contrast the two actors over the pool: `contrast M T --a A --b B --tasks pool`. The helper pairs, per pool task both actors ran, the success (higher best val) with the failure, names the one `modules/*.md` file whose text differs between the two packs (`module`), returns both texts, and the `winner`.
4. If `winner` is null, or `module` is null (no single module differs, or several do), say so and stop: the bug is not localised.
5. Otherwise write the loser's differing module with the winner's text under `runs/modular-meta/patch/modules/<file>` (your Write tool) and patch the loser: `propose M T --target <the loser> --files runs/modular-meta/patch --recipe <the winner's best pool recipe> --summary "<module> <- <winner>'s text" --visit 1`, then `gate M T <id>`. `patches: ["modules/*.md"]`: `propose` refuses any other file. `approval: gate`: the private split of the pool task decides - keep, or roll back. The eval table (`../tasks/`) is never used.
6. Answer in text with the contrast result (pairs, module, winner), the gate's verdict and the version label. Stop.

## Rules
- One module per patch. The validation split is the pool task's private split; the eval table is never used for validation.
- You never fit for yourself and never score the test split: `fit_recipe` and `score_test` are forbidden to this pack; the actors' arms in step 2 are run as the actors.

## Off switch
META_OFF: `meta: off` in `M/config.md`; nothing is contrasted and nothing lands.

## Done when
`contrast` has answered and, if a patch applied, `gate` has answered once.
