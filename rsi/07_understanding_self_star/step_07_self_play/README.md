# 07.07 · Learn what self-play does and does not provide

[Course](../../README.md) · [Theme](../README.md)

**You are here:** Theme 07, Changes and their evidence → lab 7 of 8. [Find this theme in the course map](../../COURSE-MAP.md#theme-07) · [Whole-course mindmap](../../COURSE-MAP.md#whole-course-mindmap).

## What you will build

A tiny tic-tac-toe player that learns from self-play, a saved policy table, and a frozen comparison with its untrained version.

## Why this matters

Interaction is only one part of self-play learning. You need experience, a feedback source, a parameter update, and a way to judge the resulting policy. A small game makes each part visible on a laptop.

## Before you start

Complete [07.06: Observe a collective pattern](../step_06_emergence/README.md). You need the concepts and the reports named below, not its old chat. If you start here directly, ask the tutor to prepare the listed starting state and explain the missing prerequisite first.

Open the coding agent at the repository root. Read [the tutor skill](../../skills/rsi-tutor/SKILL.md) and this lab's [brief](BRIEF.md). The agent creates a separate sibling workspace named <code>rsi-work/07-07</code> and reports its absolute path. It checks local Python and the [tool requirements](../../tools/README.md) before execution. You do not write code or configuration.

**Starting state:** The distinction between retained learning and improved performance. The agent uses the local Python environment and the supplied self-play tool; no extra agent processes are needed.

**Budget:** 3,000 training games plus 500 evaluation games per policy: 4,000 games total, CPU only. Rule tests use separate tiny fixtures. No LLM weights change. Plan about 30–45 minutes of reading and discussion; this is an author estimate, not a measured student duration. Coding-agent inference may use a paid online service. Record its cost separately when available.

## How it works

A policy is a rule for choosing an action. Here its parameters are numbers in a table indexed by board, player, and move. Both sides use the same table while playing tic-tac-toe. After a game, each visited move receives its player’s terminal return: +1 for a win, 0 for a draw, or −1 for a loss. Move the stored value one fifth of the way toward that return. This is a tabular Monte Carlo update; it does not use a neural network or a next-state value estimate. With probability 0.2, a training move explores a random legal action. Otherwise it chooses a highest-valued move, breaking ties randomly. The game rules provide feedback. Freeze the learned table before testing it against a random opponent. The table changes; the training algorithm does not. Regression and classification remain the main course project. This short game exposes the self-play mechanism directly.

**A concrete example.** In the saved author run, training game 0 ends in an O win. X’s first center move changes from value 0 to −0.2; O’s first move changes from 0 to +0.2. Each value moves 20% toward its player’s return. This does not prove the center is bad: the return includes everything that happened afterward. Later experience can revise the value.

![Self-play produces games. Terminal returns update the policy table under a fixed learning rule. Freeze the table before comparing it with the untrained policy.](../../assets/diagrams/lab-07-07.png)

*Read the diagram:* Self-play produces games. Terminal returns update the policy table under a fixed learning rule. Freeze the table before comparing it with the untrained policy.

## Run the lab

Start with this prompt. The tutor pauses for your prediction before it runs the next step.

```text
Read rsi/AGENTS.md and
rsi/skills/rsi-tutor/SKILL.md.
Guide me through lab 07.07, Learn what
self-play does and does not provide, one
step at a time.
Read its README and BRIEF. Prepare its
separate workspace.
You write and run the implementation. Keep
the reports and failures.
Ask me to predict the result before the
experiment.
```

**Make a prediction:** If two players interact but no table values change, what has been learned?

### 1. Fix the game and comparison

Keep evaluation choices outside the learning loop.

```text
Read rsi/tools/self_play.py and the
self-play section of rsi/tools/README.md.
Save the fixed protocol in my lab workspace:
3,000 training games, seed 17, exploration
0.2, learning rate 0.2, and 500 frozen games
per policy with equal X/O seats. Keep the
supplied evaluation seed schedules. Explain
legal moves, terminal returns, and the
untrained zero table. Run the small
game-rule and learning-boundary tests;
retain their result separately.
```

**Observe:** The game outcome and update rule have precise meanings before training.

### 2. Run actual self-play learning

Inspect a parameter change caused by a game.

```text
Use the supplied self-play tool to execute
this fixed experiment in a new folder in my
workspace. Keep all training moves, value
updates, episode outcomes, table files, and
evaluation traces. Apply a 60-second command
limit. Preserve a failed run instead of
overwriting it. Show one winning and one
losing player update from the saved trace.
```

**Observe:** Both players generate experience; their terminal returns change stored action values.

### 3. Inspect the frozen comparison

Separate learning from measured benefit.

```text
Read evaluation-counts.csv and
evaluation-policy-hashes.csv. Confirm 500
games per policy and equal X/O seats. Show
wins, draws, and losses overall and by seat.
Verify the policy hashes do not change
during evaluation. Plot these measured
counts and identify a remaining
trained-policy loss. Do not tune the table
or training choices after these results.
```

**Observe:** The untrained policy interacts without learning. The trained policy uses retained values without changing them during the test.

### 4. Name the mechanism

Keep the claim tied to the mutable object.

```text
Write SELF-PLAY-REPORT.md: what generated
experience, what supplied feedback, what
changed, what stayed fixed, and what the
comparison supports. Contrast this with a
proposer–critic exchange that saves only
dialogue. Explain why this run is self-play
learning but does not revise its own
learning procedure.
```

**Observe:** A changed policy and a changed improver are different experiments.

## Check your result

All 4,000 experiment games are retained. The table has actual updates, legal game traces, and unchanged evaluation hashes. Both policies use the declared evaluation schedules. The report separates this one measured comparison from claims about optimal play, other tasks, or RSI.

### Open these outputs

The agent keeps these in your lab workspace or records the original experiment path when reusing evidence.

| Output | What to inspect |
|---|---|
| RUN-CONTRACT.md and policy tables | Record the fixed training settings, initial zero policy, learned values, and freeze hash. |
| Training games and updates | Connect every state, action, terminal return, and changed parameter. |
| Evaluation counts, moves, and hashes | Retain wins/draws/losses by seat, actual failures, and unchanged policy bytes during evaluation. |
| SELF-PLAY-REPORT.md and measured plot | Explain the result, the untrained no-update counterexample, costs, and why the fixed trainer does not establish RSI. |

Ask the agent to open the actual files and show the command exit status. A written description of a run is not a run. Keep a short <code>LAB-NOTE.md</code> with your prediction, measured observation, explanation, and one limit. The tutor must mark skipped learner responses as skipped.

## Try one change

Inspect the untrained baseline: it plays 500 games but retains no parameter changes. Explain why more interaction alone would not train it. Then propose, without running, a comparison against a stronger opponent and state which earlier claim that would test.

## If something goes wrong

A header-only initial-policy.csv is intentional: absent entries have value zero. If evaluation changes the table hash, stop interpreting its score and preserve the run for diagnosis. If the tool refuses a nonempty output directory, choose a new folder; do not overwrite prior evidence. A weak result against random play is still a valid result when rules and traces check out.

Say “Stop this lab” to stop further work. Ask the agent to save <code>PROGRESS.md</code> with the last completed step and remaining budget. To resume, have it read that file and inspect active processes first. A reset creates a new sibling workspace; it does not erase failures or alter the source data. See the [recovery rules](../../tools/README.md) for interrupted tool runs.

## Key takeaways

- Self-play supplies experience that a declared learning rule can use.
- A saved parameter change shows learning; a fair comparison tests benefit.
- A fixed self-play trainer can improve a policy without recursive self-improvement.

## Research connection

[SQL-Zero, 4 September 2026](https://arxiv.org/html/2609.04697v1), offers a recent contrast: a challenger generates tasks, database execution supplies feedback, and alternating GRPO steps update the challenger and solver.

The lab retains self-generated interaction, executable outcome feedback, and actual parameter updates. Its tabular game omits SQL generation, learned curricula, LLM weights, and GRPO. It does not reproduce SQL-Zero. Inspect the author’s full run at [self-play evidence](../../evidence/2026-09-20/self-play/README.md); your own result must come from your own run.

## Check your understanding

Answer before opening the explanation. You can ask the tutor for a hint.

1. Where is the learning in this run?
2. Why is the untrained baseline a useful counterexample?
3. Does a higher win count against random play prove optimal play?
4. What would have to change to investigate RSI?

<details>
<summary>Hint</summary>

Point to an actual before/after table value. Then point to the unchanged code that updates it. Those two objects keep learning and recursive improvement distinct.

</details>

<details>
<summary>Explained answers</summary>

1. The after-game update changes retained state-action values using each player’s terminal return. The saved trace exposes those actual parameter changes.

2. It interacts with an opponent during evaluation but receives no updates. Experience and learning are separate mechanisms.

3. No. It measures performance against that opponent and schedule. A stronger opponent or a different seat can expose failures.

4. The procedure that produces improvements would need a justified revision that is inherited by later improvement work and judged under a fixed external comparison. Updating the policy table under this unchanged trainer does not do that.

</details>

## What's next

Allow a system to edit its own procedure, then ask whether the edit helps. Continue to [07.08: Make a self-modification inspectable](../step_08_modification/README.md).
