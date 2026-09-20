---
name: adult-income-meta-dream
description: "Choose the actor pack's search policy by replaying the fit log as a simulator (Dream-RSI) with zero fits, and propose the winner as the actor's Search policy line through the private gate. Use in rsi/step_10_rsi_dream after a problem's actor and verifier runs are done, before the next problem boots."
metadata:
  type: workflow
  version: "3.0"
  rsi: "on"
  approval: gate
  patches: ["SKILL.md"]
---
# Dream-RSI: the log is an exact gym for the recipes you visited, and silent elsewhere

Run every helper through the Bash tool from this lesson's directory. This pack's directory is
`.claude/skills/adult-income-meta-dream` (`M`); the target is the actor pack
`.claude/skills/adult-income` (`P`); the problem just finished is `T`.

## Boot order
1. This file. 2. `tools.md`. 3. `policies.md`: the policies you may rank. 4. `M/config.md`. The log, the cards and the actor's files come through helpers.

## Procedure
1. Build `rank_policies`, `read_pack`, `propose`, `gate`, `private_score` and `rollback` under `runs/adult-income-meta-dream/helpers/` if they are not there yet (they may import the actor's runtime helpers for the policies, the table, the split and the fit).
2. `read_pack P` and note the actor's current `Search policy:` line.
3. Rank every policy named in `policies.md` on the log of the problem just finished: `rank_policies M T --target P --policies static,obey-memory,random,neighbours-of-top-3,prefer-untried-family`. The helper replays the log: for each policy it walks the policy's first 24 picks, answers a pick from the log when the log has it, and counts a pick the log does not have as `unknown`. No fit is spent (`fits_spent: 0`, and the actor's `state.json` is unchanged). A policy's score is the best logged val among its picks; at a tie the policy with more unknown picks ranks higher, because a lap that only revisits the log learns nothing.
4. If `winner` equals the current policy line, say so and stop. Otherwise write the actor's `SKILL.md` with only the `Search policy:` line changed to the winner under `runs/adult-income-meta-dream/patch/SKILL.md` (your Write tool) and propose it with the best-val recipe of the last problem as the evidence recipe: `propose M T --target adult-income --files runs/adult-income-meta-dream/patch --recipe <recipe> --summary "policy -> <winner>: best logged val <v>, unknown <u>" --visit <n>`. `patches: ["SKILL.md"]`: `propose` refuses any other file.
5. `gate M T <id>`: the private split decides keep-or-rollback (a snapshot under `runs/adult-income/versions/gen_NNN/` first).
6. Answer in text with the ranking (policy, best logged val, visited, unknown), whether the log is `saturated`, and the gate's verdict. Stop.

## Rules
- Zero fits: `fit_recipe` is forbidden to this pack; `rank_policies` reports `fits_spent: 0` and the actor's budget counter proves it.
- You may patch the `Search policy:` line and nothing else.
- When every policy's unknown count is 0 the log is saturated: say so - the next lap will visit nothing new, and recursion pays only if it does.

## Off switch
META_OFF: `meta: off` in `M/config.md`; the actor keeps its policy line.

## Done when
`rank_policies` has answered and, if the winner differs, `gate` has answered once.
