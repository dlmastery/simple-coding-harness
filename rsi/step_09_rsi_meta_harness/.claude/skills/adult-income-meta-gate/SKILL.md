---
name: adult-income-meta-gate
description: "Improve the actor pack adult-income between two curriculum problems - one patch per visit to its Search policy line, its schema.json forbid list or its memory cards - and put it through the private gate (keep-or-rollback on a split the actor never sees; the human only reads the log). Use in rsi/step_09_rsi_meta_harness after a problem's actor and verifier runs are done, before the next problem boots."
metadata:
  type: workflow
  version: "3.0"
  rsi: "on"
  approval: gate
  patches: ["SKILL.md", "schema.json", "memory.json"]
---
# The RSI meta harness: a pack that patches the pack

Run every helper through the Bash tool from this lesson's directory. This pack's directory is
`.claude/skills/adult-income-meta-gate` (`M`); the target is the actor pack `.claude/skills/adult-income`
(`P`); the problem just finished is `T`.

## Boot order
1. This file. 2. `tools.md`. 3. `M/config.md`: the off switch. The log, the cards and the pack come through helpers.

## Procedure
1. Build `read_traces`, `read_memory`, `read_pack`, `propose`, `gate`, `private_score` and `rollback` under `runs/adult-income-meta-gate/helpers/` if they are not there yet (they may import the actor's runtime helpers for the table, the split and the fit). Read everything a meta pack may see: `read_traces P T --scope all`, `read_memory P T`, `read_pack P`.
2. Decide ONE change, the first that applies:
   a. The actor's `Search policy:` line says `static` and at least two cards are active: change that line to `Search policy: obey-memory` (the whole `SKILL.md`, with that one line changed).
   b. A field value lost every comparison one field apart it was in, at least three times across the whole log, and never won: add `{"field": ..., "value": ...}` to `schema.json -> forbid` (`hyper` values are excluded: they belong to one model each).
   c. Otherwise: the last problem's pairs yield cards the memory does not hold yet (`read_traces P T --scope problem --tally` lists `cards_by_rule`); merge at most three of them into `memory.json`.
   If none applies, say so and stop: nothing is proposed this visit.
3. Write the changed file(s) - and only those - under `runs/adult-income-meta-gate/patch/` at their paths in the pack (your Write tool), then propose the patch with the evidence recipe (the best val recipe of the last problem) and a one-line summary: `propose M T --target adult-income --files runs/adult-income-meta-gate/patch --recipe <recipe> --summary "<what and why>" --visit <n>` (`n` = the problem's index). The helper lints the patched pack against the intent, checks `patches:` and the 20 % cap, records the proposal and prints the diff; nothing has landed.
4. `gate M T <id>`: the helper snapshots the actor pack under `runs/adult-income/versions/gen_NNN/`, lands the patch, scores the evidence recipe against the incumbent (the best val recipe of the newest problem in the log) on the private split - a split no actor arm ever sees - and keeps the patch only if it did not score lower; otherwise it restores the snapshot. It prints `decision`, `before`, `after`, `keep`, `landed`.
5. Answer in text with the proposal id, the gate's numbers, whether it landed and the version label. Nobody is asked: under `approval: gate` the human reads the log (`runs/adult-income-meta-gate/<task>/traces.jsonl`) and may run `rollback adult-income gen_NNN` afterwards. Stop.

## Rules
- One proposal per visit; `propose` refuses a second (`--visit <n>` opens the next visit on the next problem).
- A patch changes at most 20 % of the pack's text and never removes the test rule from `SKILL.md`; `propose` refuses more.
- You never fit for yourself, never score the test split (`score_test` is forbidden to this pack), never touch the verifier pack or `eval.md`.

## Off switch
META_OFF: `meta: off` in `M/config.md`. You propose nothing and the actor pack stays byte-identical between problems.

## Done when
`gate` answered (kept or rolled back), or there was nothing to propose.
