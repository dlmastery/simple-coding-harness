---
name: adult-income-meta
description: Improve the actor pack adult-income between two curriculum problems - one patch per visit to its search-policy line, its schema.json forbid list or its memory cards - and put it through the human approval cycle. Use in rsi/step_09_rsi_meta_harness after a problem's actor and verifier runs are done, before the next problem boots.
metadata:
  type: workflow
  version: "2.0"
  rsi: "on"
  approval: human
  patches: ["SKILL.md", "schema.json", "memory.json"]
---
# The RSI meta harness: a pack that patches the pack

Run every command through the Bash tool from this lesson's directory. This
pack's directory is `.claude/skills/adult-income-meta` (`M`); the target is
the actor pack `.claude/skills/adult-income` (`P`); the task file of the
problem just finished is `T`.

## Boot order
1. This file. 2. `tools.md`. The log, the cards and the pack come through scripts.

## Procedure
1. Read everything a meta pack may see:
   `python ../tools/read_traces.py --pack P --task T --scope all`
   `python ../tools/read_memory.py --pack P --task T`
   `python ../tools/read_pack.py --pack P`
2. Decide ONE change, the first that applies:
   a. The actor's `Search policy:` line says `static` and at least two cards are active: change that line to `Search policy: obey-memory` (the whole `SKILL.md`, with that one line changed).
   b. A field value lost every comparison one field apart it was in, at least three times across the whole log, and never won: add `{"field": ..., "value": ...}` to `schema.json` -> `forbid` (`hyper` values are excluded: they belong to one model each).
   c. Otherwise: the last problem's pairs yield cards the memory does not hold yet (`read_traces.py --scope problem --tally` lists `cards_by_rule`); merge at most three of them into `memory.json`.
   If none applies, say so and stop: nothing is proposed this visit.
3. Write the changed file(s) - and only those - under `runs/adult-income-meta/patch/` at their paths in the pack (use your Write tool), then propose the patch with the evidence recipe (the best val recipe of the last problem) and a one-line summary:
   `python ../tools/patch_pack.py --pack M --task T --target P --files @runs/adult-income-meta/patch --recipe model=<m>,hyper=<h>,scale=<s>,encode=<e>,class_weight=<c> --summary "<what and why>"`
   The script snapshots the actor pack under `runs/adult-income/versions/gen_NNN/` and returns the diff; nothing has landed.
4. Show the user the diff and ask: **approve / edit / reject**. Wait; run nothing until the answer arrives. Then, quoting their words verbatim:
   `python ../tools/patch_pack.py --pack M --task T --target P --proposal <id> --approved "<the user's exact words>"`
   (an `edit` answer: write their version under `runs/adult-income-meta/edited/` and add `--edited @runs/adult-income-meta/edited`).
5. Answer in text with the proposal id, the decision, the version label and the files that changed. Stop. Delete nothing: `runs/adult-income-meta/patch/` is scratch.

## Rules
- One proposal per visit; the script refuses a second (`--visit <n>` opens the next visit on the next problem).
- A patch changes at most 20 % of the pack's text and never removes the test rule from `SKILL.md`; the script refuses more.
- You never fit, never score the test split (`score_test` is not in your `tools.md`), never touch the verifier pack or `eval.md`.

## Off switch
META_OFF: `{"meta": "off"}` in `M/config.json`. The script proposes nothing and the actor pack stays byte-identical between problems.

## Done when
`patch_pack.py` answered the second time (landed or rejected), or there was nothing to propose.
