---
name: adult-income-meta-dream
description: Choose the actor pack's search policy by replaying the fit log as a simulator (Dream-RSI) - zero fits - and propose the winner as the actor's `Search policy:` line. Use after a problem's actor and verifier runs are done, before the next problem boots.
metadata:
  type: workflow
  version: "1.0"
  rsi: "on"
  approval: human
  patches: ["SKILL.md"]
---
# Dream-RSI: the log is an exact gym for the recipes you visited, and silent elsewhere

## Boot order
1. This file. 2. `tools.md`. 3. `policies.md`: the policies you may rank. 4. `memory.json` of the actor pack (appended by the harness).

## Procedure
1. Call `read_traces` (scope `all`), `read_memory`, `read_pack`: the log, the cards, the actor's files - and its current `Search policy:` line.
2. Call `rank_policies` with every policy named in `policies.md`. The tool replays the log: for each policy it walks the policy's first 24 picks, answers a pick from the log when the log has it, and counts a pick the log does not have as `unknown`. No fit is spent. A policy's score is the best logged val among its picks; at a tie the policy with more unknown picks ranks higher, because a lap that only revisits the log learns nothing.
3. If the winner is the actor's current policy, say so and stop. Otherwise call `patch_pack` once: the actor's `SKILL.md` with the `Search policy:` line changed to the winner, the best-val recipe of the last problem as the evidence recipe, and a summary that names the winner's best logged val and its unknown count.
4. Answer in text with the ranking. Stop.

## Rules
- Zero fits: `fit_recipe` is not in your tools.md; `rank_policies` reports `fits_spent: 0` and the budget counter proves it.
- You may patch the `Search policy:` line and nothing else; `patch_pack` refuses any other file.
- When every policy's unknown count is 0 the log is saturated: say so - the next lap will visit nothing new.

## Off switch
META_OFF: the runner does not boot this pack; the actor keeps its policy line.

## Done when
`rank_policies` has answered and, if the winner differs, `patch_pack` has answered once.
