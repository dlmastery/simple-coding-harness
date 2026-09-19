# Lesson 10 - Dream-RSI: rank the search policies on the log, at zero fits

Dream-RSI (arXiv:2609.14858) replays experience as a simulator: instead of
spending fits to compare search strategies, the meta pack replays the fit
log and asks, for each policy in `policies.md`, what its first 24 picks
would have scored. A pick the log holds is answered for free; a pick the
log does not hold is `unknown` - the gym is exact where you have been and
silent everywhere else. `rank_policies.py` makes zero fits (the target's
budget counter is read before and after), ranks by the best logged val and
breaks ties towards the policy that would visit more new places, and the
winner is proposed as the actor's `Search policy:` line through the private
gate. The honest half of the lesson: a saturated log (`saturated: true`,
every policy's `unknown` is 0) means the next lap would learn nothing, and
the script says so instead of promising a gain. L2 in the framework's
terms: the system chooses *how* to improve; the policy library stays human.

## Getting started

Lesson 09 left the actor (policy line `static`), the verifier and the
curriculum skill. This lesson adds `.claude/skills/adult-income-meta-dream/`
(`SKILL.md`, `tools.md`, `policies.md`), extends the actor's policy menu to
the five policies of `policies.md` (`read_memory.py --order <policy>` walks
any of them), and adds one script: `../tools/rank_policies.py`. Open your
agent in this directory. Reset after a run: `echo "[]" >
.claude/skills/adult-income/memory.json`, set the actor's policy line back to
`static`, mirror to `.agents/skills/`, `rm -rf runs`.

## How to execute it

1. Type the prompt:

   ```text
   Use the adult-income-curriculum skill with the meta pack adult-income-meta-dream: run the six curriculum problems with a Dream-RSI visit after each, then the exam, and report the curve, the exam and the policy rankings.
   ```

   The meta visit after each problem is:

   ```bash
   python ../tools/rank_policies.py --pack .claude/skills/adult-income-meta-dream --task ../tasks/01_adult_income.json --target .claude/skills/adult-income --policies static,obey-memory,random,neighbours-of-top-3,prefer-untried-family
   python ../tools/patch_pack.py --pack .claude/skills/adult-income-meta-dream --task ../tasks/01_adult_income.json --target .claude/skills/adult-income --files @runs/adult-income-meta-dream/patch --recipe model=hgb,hyper=0.1,scale=yes,encode=onehot,class_weight=balanced --summary "policy -> obey-memory: best logged val 0.9172, unknown 0" --visit 1
   ```

   No approval prompt: `approval: gate`. The human reads the log.

2. Try the meta pack's limits by hand: `python ../tools/fit_recipe.py --pack
   .claude/skills/adult-income-meta-dream ...` answers `not in
   adult-income-meta-dream's tools.md`; a patch to `schema.json` answers
   `may patch ['SKILL.md'] only`.

3. Headless: `claude -p "<the prompt>" --allowedTools "Bash,Read,Write,Edit,Skill"`.
   Tests: `python run_tests.py rsi`.

## What it looks like

`.claude/skills/adult-income-meta-dream/SKILL.md`:

```markdown
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

## Procedure
2. Rank every policy named in `policies.md` on the log of the problem just finished:
   `python ../tools/rank_policies.py --pack M --task T --target P --policies static,obey-memory,random,neighbours-of-top-3,prefer-untried-family`
   The script replays the log: for each policy it walks the policy's first 24 picks, answers a pick from the log when the log has it, and counts a pick the log does not have as `unknown`. No fit is spent (`fits_spent: 0`, and the actor's budget counter is unchanged). A policy's score is the best logged val among its picks; at a tie the policy with more unknown picks ranks higher, because a lap that only revisits the log learns nothing.
3. If `winner` equals the current policy line, say so and stop.

## Rules
- Zero fits: `fit_recipe` is not in your `tools.md`; `rank_policies.py` reports `fits_spent: 0` and the budget counter proves it.
- When every policy's unknown count is 0 the log is saturated: say so - the next lap will visit nothing new, and recursion pays only if it does.
```

`../tools/rank_policies.py` - the replay:

```python
    for name in [p.strip() for p in a.policies.split(",") if p.strip()]:
        fits, tried, unknown = [], [], 0
        try:
            for n in range(1, schema["n_fits"] + 1):
                pick = next((r for r in policies.policy_order(name, static, cards, profile, fits, seed=a.seed, forbid=forbid) if r not in tried), None)
                if pick is None:
                    break
                tried.append(pick)
                if recipe.key(pick) in logged:
                    fits.append(({"recipe": pick}, {"n": n, "val_score": logged[recipe.key(pick)]}))
                else:
                    unknown += 1
```

```python
    ranked.sort(key=lambda e: (-(e["best_logged_val"] or 0), -e["unknown"]))
```

The recorded run (Claude Code 2.1.278, headless, 70 turns, 1495 s; the
arms' fit calls trimmed to the visits and the tables):

```text
[Skill adult-income-curriculum]
agent> Verifier: 9 cards written, 9 new, 0 demoted. Now the Dream-RSI visit 1 on problem 01.
$ python ../tools/rank_policies.py --pack .claude/skills/adult-income-meta-dream --task ../tasks/01_adult_income.json --target .claude/skills/adult-income --policies static,obey-memory,random,neighbours-of-top-3,prefer-untried-family
{"ranking": [{"policy": "obey-memory", "best_logged_val": 0.9172, "visited": 10, "unknown": 14, ...}, {"policy": "neighbours-of-top-3", "best_logged_val": 0.9172, "unknown": 6, ...}, {"policy": "static", "best_logged_val": 0.9172, "visited": 24, "unknown": 0, ...}, ...],
 "winner": "obey-memory", "fits_spent": 0, "log_size": 24, "saturated": false, "current_policy": "static"}
agent> Winner obey-memory != current static, so I write the patched SKILL.md (only the policy line changed)
and propose it through the gate.
$ python ../tools/patch_pack.py --pack .claude/skills/adult-income-meta-dream --task ../tasks/01_adult_income.json --target .claude/skills/adult-income --files @runs/adult-income-meta-dream/patch --recipe model=hgb,hyper=0.1,scale=yes,encode=onehot,class_weight=balanced --summary "policy -> obey-memory: best logged val 0.9172, unknown 14" --visit 1
{"id": "g1", "decision": "y", "approved_by": "gate", "gate": {"before": 0.8951, "after": 0.8951, "keep": true}, "landed": true, "version": "gen_001", "files": ["SKILL.md"], ...}
agent> Visit 1: gate kept (private 0.8951 -> 0.8951), landed as gen_001, policy now obey-memory.
agent> Visit 2: gate kept (1.0 -> 1.0), gen_002, policy now random.
agent> Visit 3: kept, gen_003, policy neighbours-of-top-3.
agent> Visit 4: kept (private 0.9985 -> 0.9994), gen_004, policy obey-memory.
agent> Visit 5: kept (0.9323 -> 0.9395), gen_005, policy neighbours-of-top-3.
agent> Visit 6: kept (0.5806 -> 0.8817), gen_006, policy random. All six problems done - the learning curve.
$ python ../tools/curve.py --pack .claude/skills/adult-income --tasks ../tasks
 # problem                 mem val  ctl val     gap  mem test  ctl test wasted m/c cards +/-/act
 1 adult_income             0.9172   0.9172 +0.0000    0.9034    0.9034   16/16      9/0/10
 2 breast_cancer            0.9966   0.9954 +0.0012    0.9883    0.9844    0/0       6/0/10
 3 wine                        1.0      1.0 +0.0000       1.0       1.0    0/0       0/0/10
 4 digits                   0.9995    0.999 +0.0005     0.999    0.9984    0/0       4/0/10
 5 synth_shift_a            0.9531   0.9507 +0.0024    0.9178    0.9181    1/0       5/1/10
 6 synth_shift_b            0.8571   0.7925 +0.0646    0.9104     0.834   17/17      2/1/10
$ python ../tools/exam.py --pack .claude/skills/adult-income --task ../tasks/07_exam.json --seeds 0,1,2,3,4
memory arm beats control on 4 of 5 seeds (3 on test score, 1 same score won by fewer wasted fits), mean test gap 0.0282; pack unchanged: True; no card written: True
agent> Dream-RSI visits (all zero fits, fits_spent: 0 every time):
| visit | problem | ranking (policy: best logged val / unknown) | proposal | gate | version |
| 1 | adult_income | obey-memory 0.9172/14, neighbours 0.9172/6, static 0.9172/0, prefer-untried 0.9172/0, random 0.915/17 | static -> obey-memory | keep 0.8951 -> 0.8951 | gen_001 |
| 2 | breast_cancer | random 0.9966/17, prefer-untried 0.9954/20, static 0.9954/14, neighbours 0.9954/14, obey-memory 0.9954/2 (stopped early) | obey-memory -> random | keep 1.0 -> 1.0 | gen_002 |
| 3 | wine | neighbours 1.0/18, static 1.0/17, prefer-untried 1.0/17, random 1.0/0, obey-memory none/3 (stopped early) | random -> neighbours-of-top-3 | keep 1.0 -> 1.0 | gen_003 |
| 4 | digits | obey-memory 0.999/16, random 0.999/16, neighbours 0.999/9, prefer-untried 0.999/9, static 0.999/8 | neighbours -> obey-memory | keep 0.9985 -> 0.9994 | gen_004 |
| 5 | synth_shift_a | neighbours 0.9531/6, random 0.9528/18, prefer-untried 0.9507/20, static 0.9507/14, obey-memory 0.9507/2 (stopped early) | obey-memory -> neighbours-of-top-3 | keep 0.9323 -> 0.9395 | gen_005 |
| 6 | synth_shift_b | random 0.8571/17, obey-memory 0.8571/12, neighbours 0.8571/7, prefer-untried 0.7925/16, static 0.7925/8 | neighbours -> random | keep 0.5806 -> 0.8817 | gen_006 |
The log was never saturated (some policy always had unknown picks), and every one of the six proposals was
kept - the gate never rolled one back. Note that the winner flipped on every visit; the ranking rewards
the policy that would revisit the fewest logged recipes, so it tends to pick whatever the previous policy wasn't.
[70 turns, 1495 s]
```

What to notice, honestly: the curve's gaps are lesson 07's except digits
(+0.0005) and the wasted fits on problem 6 (17 under `neighbours-of-top-3`
where `obey-memory` wasted 3), and the exam's mean test gap is +0.0282
against lesson 07's +0.0308. Dream-RSI's ranking is exact where the log
has been and rewards leaving it; on a log that one policy wrote, the
policy that *did not* write it ranks first at every tie, so the line
flipped six times in six visits - `static -> obey-memory -> random ->
neighbours-of-top-3 -> obey-memory -> neighbours-of-top-3 -> random` - and
the gate kept each flip because the evidence recipe is the log's best
recipe under either policy. The replay is a gym for the recipes you
visited and silent elsewhere; it does not know which policy *found*
them. That is the paper's point about "reliable verification", and this
page reports it rather than smoothing it over.

Files:

```text
step_10_rsi_dream/
├── README.md, test_step.py, .claude/settings.json
├── .claude/skills/adult-income/              the actor: policy line `static`, five policies described
├── .claude/skills/adult-income-verifier/
├── .claude/skills/adult-income-curriculum/   names the dream meta pack
├── .claude/skills/adult-income-meta-dream/   SKILL.md, tools.md, policies.md
├── .agents/skills/...
└── runs/{adult-income, adult-income-meta-dream}/   (after a run)
```

## Governance considerations

- **Who approves what.** The private gate, per visit; the policy library
  (`policies.md`) is the human's and the meta pack may not add to it.
- **The hook.** The locked test; no human call in this lesson.
- **What the script refuses.** A fit for the meta pack; a patch to any file
  but `SKILL.md`; a second proposal per visit; a patch the private split
  scores lower.
- **What is and is not self-modified.** The actor's `Search policy:` line
  (one line of its `SKILL.md`), through a snapshot and the gate. The five
  policies' definitions, the cards' rule and the verifier are not.

## How to measure it

| Claim | Test |
|---|---|
| `rank_policies` spends zero fits (the state is byte-identical), `static` replays the log fully, `random` and `neighbours-of-top-3` leave it (`unknown` > 0), the meta pack cannot fit | `test_rank_policies_spends_zero_fits_and_marks_unknown` |
| the winner becomes the policy line through the gate; the next lap visits recipes the log did not hold; any other file is refused | `test_winner_becomes_the_policy_line_and_the_next_lap_visits_new_recipes` |
| a saturated log is reported as such | `test_saturated_log_is_reported` |
| the pack contract | `test_pack_contract` |
| the recorded run reproduces (`RSI_LIVE=1`) | `test_live_claude_code` |

Run: `python run_tests.py rsi` from the repo root.

## Next lesson

[Lesson 11 - RSIAgent](../step_11_rsi_agent/README.md): the next experiment,
chosen on purpose. Previous:
[Lesson 09 - the RSI meta harness](../step_09_rsi_meta_harness/README.md).
