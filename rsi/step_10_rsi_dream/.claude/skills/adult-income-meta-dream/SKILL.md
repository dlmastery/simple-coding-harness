---
name: adult-income-meta-dream
description: Choose the actor pack's search policy by replaying the fit log as a simulator (Dream-RSI) with zero fits, and propose the winner as the actor's Search policy line through the private gate. Use in rsi/step_10_rsi_dream after a problem's actor and verifier runs are done, before the next problem boots.
metadata:
  type: workflow
  version: "2.0"
  rsi: "on"
  approval: gate
  patches: ["SKILL.md"]
---
# Dream-RSI: the log is an exact gym for the recipes you visited, and silent elsewhere

Run every command through the Bash tool from this lesson's directory. This
pack's directory is `.claude/skills/adult-income-meta-dream` (`M`); the
target is the actor pack `.claude/skills/adult-income` (`P`); the task file
of the problem just finished is `T`.

## Boot order
1. This file. 2. `tools.md`. 3. `policies.md`: the policies you may rank. The log, the cards and the actor's files come through scripts.

## Procedure
1. `python ../tools/read_pack.py --pack P --checksums` and note the actor's current `Search policy:` line (`grep "Search policy:" P/SKILL.md`).
2. Rank every policy named in `policies.md` on the log of the problem just finished:
   `python ../tools/rank_policies.py --pack M --task T --target P --policies static,obey-memory,random,neighbours-of-top-3,prefer-untried-family`
   The script replays the log: for each policy it walks the policy's first 24 picks, answers a pick from the log when the log has it, and counts a pick the log does not have as `unknown`. No fit is spent (`fits_spent: 0`, and the actor's budget counter is unchanged). A policy's score is the best logged val among its picks; at a tie the policy with more unknown picks ranks higher, because a lap that only revisits the log learns nothing.
3. If `winner` equals the current policy line, say so and stop. Otherwise write the actor's `SKILL.md` with only the `Search policy:` line changed to the winner under `runs/adult-income-meta-dream/patch/SKILL.md` (use your Write tool) and propose it with the best-val recipe of the last problem as the evidence recipe:
   `python ../tools/patch_pack.py --pack M --task T --target P --files @runs/adult-income-meta-dream/patch --recipe model=<m>,hyper=<h>,scale=<s>,encode=<e>,class_weight=<c> --summary "policy -> <winner>: best logged val <v>, unknown <u>" --visit <n>`
   `approval: gate`: the private split decides keep-or-rollback; `patches: ["SKILL.md"]`: the script refuses any other file.
4. Answer in text with the ranking (policy, best logged val, visited, unknown), whether the log is `saturated`, and the gate's verdict. Stop.

## Rules
- Zero fits: `fit_recipe` is not in your `tools.md`; `rank_policies.py` reports `fits_spent: 0` and the budget counter proves it.
- You may patch the `Search policy:` line and nothing else.
- When every policy's unknown count is 0 the log is saturated: say so - the next lap will visit nothing new, and recursion pays only if it does.

## Off switch
META_OFF: `{"meta": "off"}` in `M/config.json`; the actor keeps its policy line.

## Done when
`rank_policies.py` has answered and, if the winner differs, `patch_pack.py` has answered once.
