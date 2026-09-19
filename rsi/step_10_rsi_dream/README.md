# Lesson 10 - Dream-RSI: rank the search policies on the log, at zero fits

Dream-RSI (arXiv:2609.14858) replays experience as a simulator to choose
how to search next. Here that is one tool, `rank_policies`: for every policy
named in `policies.md` it walks the policy's first 24 picks against this
problem's log, answers a pick from the log when the log has it, counts a
pick the log does not have as *unknown*, and spends no fit - the budget
counter proves it. A policy's score is the best logged val among its picks;
at a tie the policy with more unknown picks ranks higher, because a lap that
only revisits the log learns nothing. The meta pack proposes the winner as
the actor's `Search policy:` line through lesson 09's cycle, and the next
lap grows the log. The lesson is the limit as much as the trick: history is
an exact gym for the recipes you visited and silent everywhere else, an
adaptive policy stops replaying at its first unknown, and on a problem where
everything ties the ranking rewards novelty alone.

## Getting started

Lesson 09 left the actor with its policy line, the verifier, and the meta
cycle. This lesson adds `skills/adult-income-meta-dream/` (a meta pack whose
`patches:` allow-list is `SKILL.md` only) with `policies.md`, the tool
`rank_policies`, and `common/policies.py` - the one function that says what
order each named policy would try recipes in, shared by the fake model and
the replay. The Dream-RSI search-policy line replaces lesson 09's rule (a).

## How to execute it

1. The curriculum with a Dream-RSI visit after every problem:

   ```bash
   cd rsi/step_10_rsi_dream
   FAKE_MODEL=1 python run.py
   FAKE_MODEL=1 HUMAN=script:y,y,y,y,y,y python run.py     # scripted approvals
   ```

   ```powershell
   cd rsi\step_10_rsi_dream
   $env:FAKE_MODEL = "1"; python run.py
   ```

   At each `approve p1 (patch)? [y/n/edit]` the diff is one line - the
   policy - and the summary names the winner's best logged val and its
   unknown count. `y` lands it, `n` keeps the current policy.
2. Tests: `python run_tests.py rsi`.

## What it looks like

`skills/adult-income-meta-dream/SKILL.md`:

```markdown
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
```

```markdown
2. Call `rank_policies` with every policy named in `policies.md`. The tool replays the log: for each policy it walks the policy's first 24 picks, answers a pick from the log when the log has it, and counts a pick the log does not have as `unknown`. No fit is spent. A policy's score is the best logged val among its picks; at a tie the policy with more unknown picks ranks higher, because a lap that only revisits the log learns nothing.
```

`skills/adult-income-meta-dream/policies.md`:

```markdown
- `static`: walk `schema.json` -> `recipes` in order, cards or no cards.
- `obey-memory`: probe one recipe per model (the believed model first) with the preferred preprocessing; then the believed family - its static recipes, then its hyper variants - ranked by the cards; then the rest of the grid.
- `random`: the 72-recipe grid in a seeded shuffle.
- `neighbours-of-top-3`: six static fits, then the untried neighbours (one field away) of the three best so far, then the static list.
- `prefer-untried-family`: at every step the model family with the fewest fits so far, static recipes before hyper variants.
```

The replay:

`../common/tools.py`:

```python
    rows = run.trace.rows("fit", problem=run.problem)
    logged = {recipe.key(r["recipe"]): r["val_score"] for r in rows if r["val_score"] is not None}
```

```python
            tried.append(pick)
            if recipe.key(pick) in logged:      # the log answers for free
                fits.append(({"recipe": pick}, {"n": n, "val_score": logged[recipe.key(pick)]}))
            else:                               # the gym is silent here: the policy would have to fit to know
                unknown += 1
```

```python
    ranking.sort(key=lambda e: (-(e["best_logged_val"] or 0), -e["unknown"]))
```

Expected output, on this machine (`FAKE_MODEL=1 HUMAN=script:y,y,y,y,y,y`;
the prompts are elided):

```text
 # problem                 mem val  ctl val     gap  mem test  ctl test wasted m/c cards +/-/act
 1 adult_income             0.9172   0.9172 +0.0000    0.9034    0.9034   16/16      4/0/4
 2 breast_cancer            0.9966   0.9954 +0.0012    0.9883    0.9844    0/0       3/0/7
 3 wine                        1.0      1.0 +0.0000       1.0       1.0    0/0       1/0/8
 4 digits                   0.9991    0.999 +0.0001    0.9988    0.9984    0/0       1/0/9
 5 synth_shift_a            0.9507   0.9507 +0.0000    0.9181    0.9181    9/0       4/1/12
 6 synth_shift_b            0.8571   0.7925 +0.0646    0.9104     0.834    4/17      1/0/13
  after problem 1: log 24 recipes, fits spent 0; winner obey-memory (best logged 0.9172, unknown 14); patch {"id": "p1", "decision": "y", "gate": null, "landed": true, "version": "gen_001", "files": ["SKILL.md"]}
  after problem 2: log 38 recipes, fits spent 0; winner random (best logged 0.9966, unknown 12); patch {"id": "p1", "decision": "y", "gate": null, "landed": true, "version": "gen_002", "files": ["SKILL.md"]}
  after problem 3: log 42 recipes, fits spent 0; winner random (best logged 1.0, unknown 12); patch null
  after problem 4: log 41 recipes, fits spent 0; winner random (best logged 0.9991, unknown 12); patch null
  after problem 5: log 41 recipes, fits spent 0; winner obey-memory (best logged 0.9507, unknown 9); patch {"id": "p1", "decision": "y", "gate": null, "landed": true, "version": "gen_003", "files": ["SKILL.md"]}
  after problem 6: log 38 recipes, fits spent 0; winner random (best logged 0.8571, unknown 12); patch {"id": "p1", "decision": "y", "gate": null, "landed": true, "version": "gen_004", "files": ["SKILL.md"]}
policy line now: Search policy: random
```

Read it against lesson 09's curve. After problem 1 the replay picks
`obey-memory` (the same best, more unvisited picks) and problem 2 improves
as before. After problem 2 the replay credits `random` with the 0.9966 that
`obey-memory` actually found - a replay gives a policy credit for any logged
recipe it happens to pick - and the actor runs random on problems 3 and 4,
where everything ties anyway. After problem 5 `obey-memory` wins again,
problem 6 repeats lesson 09's +0.065, and the replay on problem 6's log
hands the line back to `random` for whatever comes next. Zero fits were
spent on any of these decisions; the trace row `rank_policies` says
`fits_spent: 0` each time. That is the method and its price in one table.

Files:

```text
step_10_rsi_dream/
  skills/adult-income/              lesson 09's actor (Search policy: static, an empty forbid list)
  skills/adult-income-verifier/     lesson 09's verifier
  skills/adult-income-meta-dream/
    SKILL.md                        read log, cards, pack; rank_policies; patch the policy line to the winner
    tools.md                        Allowed: read_traces, read_memory, read_pack, rank_policies, patch_pack
    policies.md                     the five policies and what each does
  run.py                            the curriculum with a Dream-RSI visit after every problem
  test_step.py                      the claims below
  README.md                         this lesson
```

## Governance considerations

- Who approves what: the human approves each policy change (`approval:
  human`); the ranking itself is the model's, made on the log alone.
- Off switches: `META_OFF`; `n` at the prompt; `versions/` as in lesson 09.
- What the model may not do, and which tool enforces it: fit during the
  ranking (`fit_recipe` is not in its `tools.md`; `rank_policies` never
  calls `do_fit`); patch anything but `SKILL.md` (`patches: ["SKILL.md"]`,
  enforced by `patch_pack`); name a policy that does not exist
  (`policy_order` raises, `execute` returns the error).
- What is and is not self-modified: the actor's `Search policy:` line.
  The policy library (`policies.md`, `common/policies.py`) is the human's:
  the system chooses among strategies it did not write. Rung: L2 (how to
  improve), with the acceptance rule human.

## How to measure it

| Claim | Test |
|---|---|
| `rank_policies` makes zero fits (the budget counter and the trace prove it); the meta pack cannot fit | `test_rank_policies_makes_zero_fits` |
| a policy preferring unvisited recipes scores unknown; `static` on its own log has none; an unknown policy name is an error | `test_a_policy_preferring_unvisited_recipes_scores_unknown` |
| the winner is proposed as the search-policy line, lands under `y`, and the next lap adds recipes the log never saw | `test_the_winner_is_proposed_and_the_next_lap_visits_new_recipes` |

Scorecard fields reported: all fourteen per problem and arm, plus the
`rank_policies` trace rows (ranking, `fits_spent`, log size). Run
`python run_tests.py rsi` from the repo root.

## Next lesson

Next: [11 - RSIAgent](../step_11_rsi_agent/README.md): the next experiment
chosen on purpose, broad then deep, memory frozen at test. Previous:
[09 - the RSI meta harness](../step_09_rsi_meta_harness/README.md).
